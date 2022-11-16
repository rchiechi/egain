#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Sub programs for communication using PyVisa

author : Eoin O'Farrell
email : phyoec@nus.edu.sg
last edit : January 2015
forked from https://github.com/HuangJunye/GrapheneLab-Measurement-Code.git

Edited to support PyVisa 1.6

Functions written:
    InitializeGPIB
    InitialIzeSerial

"""
import os
import platform
import time
from contextlib import contextmanager
import pyvisa as visa
import serial
rm = visa.ResourceManager()

MODE_GPIB = 'GPIB'
MODE_SERIAL = 'SERIAL'

def initialize_gpib(address, board, query_id=True, read_termination="LF", **kwargs):
    """ Initalize GPIB devices using PyVisa """

    gpib_name = f"GPIB{board}::{address}::INSTR"
    try:
        gpib_visa = rm.open_resource(gpib_name)
        if read_termination == "LF":
            gpib_visa.read_termination = "\n"
            gpib_visa.write_termination = "\n"
        elif read_termination == "CR":
            gpib_visa.read_termination = "\r"
            gpib_visa.write_termination = "\r"
        elif read_termination == "CRLF":
            gpib_visa.read_termination = "\r\n"
            gpib_visa.write_termination = "\r\n"
        for kw in list(kwargs.keys()):
            tmp = "".join(("gpib_visa.", kw, "=", kwargs[kw]))
            exec(tmp)
        if query_id:
            print(gpib_visa.query("*IDN?"))
    except Exception:
        print("Failed opening GPIB address %d\n" % address)
        gpib_visa = None
    return gpib_visa


def initialize_serial_visa(name, idn="*IDN?", read_termination="LF", **kwargs):
    """ Initialize Serial devices using PyVisa """

    try:
        print(f"Opening {name}")
        serial_visa = rm.open_resource(name)
        print("Setting timeout")
        serial_visa.timeout = 5000  # 5s
        print("Setting read_termination")
        if read_termination == "LF":
            serial_visa.read_termination = "\n"
        elif read_termination == "CR":
            serial_visa.read_termination = "\r"
        elif read_termination == "CRLF":
            serial_visa.read_termination = "\r\n"
        for kw in list(kwargs.keys()):
            tmp = "".join(("serial_visa.", kw, "=", kwargs[kw]))
            exec(tmp)
        print(f"Sending {idn}")
        print(serial_visa.query(idn))
    except Exception:
        print("Failed opening serial port %s\n" % name)
        serial_visa = None
    return serial_visa

def initialize_serial(name, idn="*IDN?", read_termination="LF", **kwargs):
    """ Initialize Serial devices using PyVisa """

    try:
        print(f"Opening {name}")
        serial_visa = SerialVisa(visatoserial(name))
        print("Setting timeout")
        serial_visa.timeout = 5000  # 5s
        print("Setting read_termination")
        if read_termination == "LF":
            serial_visa.read_termination = "\n"
        elif read_termination == "CR":
            serial_visa.read_termination = "\r"
        elif read_termination == "CRLF":
            serial_visa.read_termination = "\r\n"
        for kw in list(kwargs.keys()):
            tmp = "".join(("serial_visa.", kw, "=", kwargs[kw]))
            exec(tmp)
        print(f"Sending {idn}")
        print(serial_visa.query(idn))
    except Exception as msg:
        print("Failed opening serial port %s\n" % name)
        print(str(msg))
        serial_visa = None
    return serial_visa

@contextmanager
def _mutestderr():
    original_stderr = os.dup(2)  # stderr stream is linked to file descriptor 2, save a copy of the real stderr so later we can restore it
    blackhole = os.open(os.devnull, os.O_WRONLY)  # anything written to /dev/null will be discarded
    os.dup2(blackhole, 2)  # duplicate the blackhole to file descriptor 2, which the C library uses as stderr
    os.close(blackhole)  # blackhole was duplicated from the line above, so we don't need this anymore
    yield
    os.dup2(original_stderr, 2)  # restoring the original stderr
    os.close(original_stderr)

def enumerateDevices():
    _devs = []
    _filter = ['']
    if platform.system() == 'Linux':
        _filter == ['ttyUSB', 'GPIB']
    rm = visa.ResourceManager('@py')
    with _mutestderr():
        for _dev in rm.list_resources():
            for _f in _filter:
                if _f.lower() in _dev.lower():
                    _devs.append(_dev)
    return _devs

def visatoserial(visa_address):
    _path = visa_address.split(':')[0].split('/')
    return f"/{'/'.join(_path[1:])}"

#     if MEAS_MODE == MODE_GPIB:
#         return _enumerateVISA()
#     elif MEAS_MODE == MODE_SERIAL:
#         return _enumerateSERIAL()
#     else:
#         return []
# 
# def _enumerateSERIAL():
#     _filter = ''
#     if platform.system() == "Darwin":
#         _filter = 'usbmodem'
#     if platform.system() == "Linux":
#         _filter = 'ttyUSB'
#     _devs = []
#     for _dev in os.listdir('/dev'):
#         if _filter.lower() in _dev.lower():
#             _devs.append(_dev)
#     return _devs
# 
# def _enumerateVISA():
#     _devs = []
#     rm = visa.ResourceManager('@py')
#     with _mutestderr():
#         for _dev in rm.list_resources():
#             _devs.append(_dev)
#     return _devs

class SerialVisa():

    buffer = []
    timeout_s = 1
    read_termination = "\n"
    write_termination = "\r\n"
    smu = None

    def __init__(self, address, baud=9600, timeout=1):
        self.delta = time.time()
        self.address = address
        self.baud = baud
        self.timeout = timeout
        self.smu = serial.Serial(address, baud, timeout=timeout)

    @property
    def timeout(self):
        return self.timeout_s*1000

    @timeout.setter
    def timeout(self, ms):
        self.timeout_s = ms/1000.0
        if self.smu is not None:
            self.smu.timeout = self.timeout_s

    def __delay(self):
        if time.time() - self.delta < 1:
            time.sleep(1)
        self.delta = time.time()

    def write(self, cmd):
        self.__delay()
        self.smu.write(bytes(cmd, encoding='ascii'))

    def query(self, cmd):
        self.__delay()
        result = self.smu.write(bytes(cmd, encoding='ascii'))
        if len(self.buffer) > 100:
            self.buffer = self.buffer[-100:]
        self.buffer.append(str(result))
        return self.buffer[-1]
