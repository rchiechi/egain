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
import threading
from contextlib import contextmanager
import pyvisa as visa
import serial
from gui.main import DEBUG
from meas.notes import Music
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


def initialize_serial_pyvisa(name, idn="*IDN?", read_termination="LF", **kwargs):
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

def initialize_serial(name, idn="*IDN?", read_termination="CR", **kwargs):
    """ Initialize Serial devices using SerialVisa """

    try:
        print(f"Opening {name}")
        serial_visa = SerialVisa(visatoserial(name))
        # print("Setting timeout")
        # serial_visa.timeout = 2000  # 2s
        # print("Setting read_termination")
        # if read_termination == "LF":
        #     serial_visa.read_termination = "\n"
        # elif read_termination == "CR":
        #     serial_visa.read_termination = "\r"
        # elif read_termination == "CRLF":
        #     serial_visa.read_termination = "\r\n"
        # for kw in list(kwargs.keys()):
        #     tmp = "".join(("serial_visa.", kw, "=", kwargs[kw]))
        #     exec(tmp)
        i = 0
        while i < 5:
            IDN = serial_visa.query(idn)
            if IDN:
                print(IDN)
                serial_visa.playchord()
                break
            else:
                serial_visa.close()
                time.sleep(1)
                serial_visa.open()
                i += 1

    except Exception as msg:
        print("Failed opening serial port %s" % name)
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


class SerialVisa():

    buffer = {}
    encoding = 'ascii'
    timeout_s = 1
    read_termination_b = b"\n"
    write_termination_b = b"\r"
    cmd_delay = 0.5
    smu = None

    def __init__(self, address, baud=9600, timeout=1):
        self.delta = time.time()
        self.address = address
        self.baud = baud
        self.timeout = timeout
        self.smu = serial.Serial(address, baud, timeout=timeout)
        # self.playchord()

    @property
    def timeout(self):
        return self.timeout_s*1000

    @timeout.setter
    def timeout(self, ms):
        self.timeout_s = ms/1000.0
        if self.smu is not None:
            # print(self.timeout_s)
            self.smu.timeout = self.timeout_s

    @property
    def read_termination(self):
        return str(self.read_termination_b, encoding=self.encoding)

    @read_termination.setter
    def read_termination(self, c):
        # print(bytes(c, encoding=self.encoding))
        self.read_termination_b = bytes(c, encoding=self.encoding)

    @property
    def write_termination(self):
        return str(self.write_termination_b, encoding=self.encoding)

    @write_termination.setter
    def write_termination(self, c):
        self.write_termination_b = bytes(c, encoding=self.encoding)

    def __delay(self):
        if time.time() - self.delta < self.cmd_delay:
            time.sleep(self.cmd_delay)
        self.delta = time.time()

    def __writebutter(self, cmd_, data_):
        # print(data_)
        self.buffer[cmd_] = []
        for _d in data_.split(self.read_termination_b):
            # print(_d)
            if _d not in self.buffer:
                self.buffer[cmd_].append(str(_d.strip(self.read_termination_b),
                                         encoding=self.encoding))
        # print(self.buffer)

    def close(self):
        self.smu.close()

    def open(self):
        self.smu.open()

    def playchord(self):
        self.smu.write(b':SYST:BEEP:STAT ON'+self.write_termination_b)
        self.smu.write(b'SYST:BEEP:IMM 261.63,0.25'+self.write_termination_b)
        time.sleep(0.25)
        # self.smu.write(b'SYST:BEEP:IMM 329.63,0.25'+self.write_termination_b)
        # time.sleep(0.25)
        # self.smu.write(b'SYST:BEEP:IMM 392.00,0.25'+self.write_termination_b)
        # time.sleep(0.25)
        # self.smu.write(b'SYST:BEEP:IMM 523.25,1'+self.write_termination_b)
        # time.sleep(1)

    def write(self, cmd):
        self.__delay()
        self.smu.write(bytes(cmd, encoding=self.encoding)+self.write_termination_b)
        if DEBUG:
            print(f'>> {bytes(cmd, encoding=self.encoding)+self.write_termination_b}')

    def query(self, cmd):
        self.__delay()
        self.write(cmd)
        if len(self.buffer) > 100:
            self.buffer = self.buffer[-100:]
        self.__writebutter(cmd, self.smu.read_until(self.read_termination_b))
        if DEBUG:
            print(f'<< {self.buffer[cmd][-1]}')
        return self.buffer[cmd][-1]

    def get_wait_for_meas(self):
        self.write('*OPC?')
        alive = threading.Event()
        alive.set()
        opcthread = OPCThread(self.smu, alive)
        return alive, opcthread
        # opcthread = OPCThread(self.smu, alive)
        # # _s = self.smu.read(1)
        # while self.smu.read(1) != b'1':
        #     # print(_s)
        #     time.sleep(1)
        #     # _s = self.smu.read(1)
        # self.smu.read(1)  # Trim CR


class OPCThread(threading.Thread):

    def __init__(self, smu, alive):
        super().__init__()
        self.smu = smu
        self.alive = alive

    def run(self):
        while self.alive.is_set():
            _s = self.smu.read(1)
            # print(_s)
            if _s == b'1':
                print(self.smu.read(1))  # Trim CR
                break
            time.sleep(1)
        # self.smu.end_voltage_sweep()
