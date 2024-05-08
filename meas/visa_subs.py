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
import sys
import logging
import time
import threading
from contextlib import contextmanager
# import pyvisa as visa
import serial
# rm = visa.ResourceManager()

logger = logging.getLogger(__package__+'.visa')

MODE_GPIB = 'GPIB'
MODE_SERIAL = 'SERIAL'

def initialize_gpib(address, board, query_id=True, read_termination="LF", **kwargs):
    logger.error("GPBIB not implemented.")
    sys.exit()


def initialize_serial(name, idn="*IDN?", read_termination="CR", **kwargs):
    """ Initialize Serial devices using SerialVisa """

    try:
        logger.info(f"Opening serial device {name}")
        serial_visa = SerialVisa(visatoserial(name), flowcontrol=kwargs.get("flowcontrol", False))
        serial_visa.timeout = 500
        i = 0
        while i < 5:
            logger.debug(idn)
            serial_visa.write(idn)
            IDN = b''
            _c = serial_visa.read(1)
            while _c:
                IDN += _c
                _c = serial_visa.read(1)
            # IDN = serial_visa.read(128)
            if IDN:
                logger.info(IDN)
                if not kwargs.get('quiet', False):
                    serial_visa.playchord()
                serial_visa.timeout = 1000
                return serial_visa
            else:
                serial_visa.close()
                time.sleep(1)
                serial_visa.open()
                i += 1

    except Exception as msg:
        logger.warning(f"Exception: {str(msg)}")
    logger.error("Failed opening serial port %s" % name)
    return None

@contextmanager
def _mutestderr():
    original_stderr = os.dup(2)  # stderr stream is linked to file descriptor 2, save a copy of the real stderr so later we can restore it
    blackhole = os.open(os.devnull, os.O_WRONLY)  # anything written to /dev/null will be discarded
    os.dup2(blackhole, 2)  # duplicate the blackhole to file descriptor 2, which the C library uses as stderr
    os.close(blackhole)  # blackhole was duplicated from the line above, so we don't need this anymore
    yield
    os.dup2(original_stderr, 2)  # restoring the original stderr
    os.close(original_stderr)


# def enumerateDevices():
#     _devs = []
#     _filter = ['']
#     if platform.system() == 'Linux':
#         _filter == ['ttyUSB', 'GPIB']
#     rm = visa.ResourceManager('@py')
#     with _mutestderr():
#         for _dev in rm.list_resources():
#             if 'Bluetooth' in _dev:
#                 continue
#             for _f in _filter:
#                 if _f.lower() in _dev.lower():
#                     _devs.append(_dev)
#     return _devs


def visatoserial(visa_address):
    if os.name == "nt":
        return visa_address.strip()
    else:
        _path = visa_address.split(':')[0].split('/')
        return f"/{'/'.join(_path[1:])}"


class SerialVisa():

    buff = []
    encoding = 'ascii'
    timeout_s = 1
    read_termination_b = b"\n"
    write_termination_b = b"\r"
    cmd_delay = 0.05
    smu = None
    lock = threading.Lock()

    def __init__(self, address, baud=9600, flowcontrol=False):
        self.delta = time.time()
        # self.address = address
        # self.timeout = timeout
        self.smu = serial.Serial(address, baud, timeout=1, xonxoff=flowcontrol)
        # self.playchord()

    @property
    def timeout(self):
        return self.timeout_s*1000

    @timeout.setter
    def timeout(self, ms):
        if self.smu is not None:
            self.timeout_s = ms/1000.0
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

    def __writebuffer(self, cmd_, data_):
        # print(data_)
        # if len(self.buff) > 100:
        #     self.buff = self.buff[-100:]
        for _d in data_.split(self.read_termination_b):
            if _d:
                logger.debug(_d)
                self.buff.append((cmd_, str(_d, encoding=self.encoding)))

    @property
    def buffer(self):
        return self.buff

    @property
    def lastreading(self):
        if len(self.buff):
            return self.buff.pop()[1]
        else:
            return ''

    def close(self):
        self.smu.close()

    def open(self):
        self.smu.open()

    def playchord(self):
        with self.lock:
            self.smu.write(b':SYST:BEEP:STAT ON'+self.write_termination_b)
            self.smu.write(b'SYST:BEEP:IMM 261.63,0.25'+self.write_termination_b)
            time.sleep(0.25)
            self.smu.write(b'SYST:BEEP:IMM 329.63,0.25'+self.write_termination_b)
            time.sleep(0.25)
            self.smu.write(b'SYST:BEEP:IMM 392.00,0.25'+self.write_termination_b)
            time.sleep(0.25)
            self.smu.write(b'SYST:BEEP:IMM 523.25,1'+self.write_termination_b)
            time.sleep(0.5)

    def write(self, cmd):
        self.__delay()
        with self.lock:
            self.smu.write(bytes(cmd, encoding=self.encoding)+self.write_termination_b)
            logger.debug(f'>> {bytes(cmd, encoding=self.encoding)+self.write_termination_b}')

    def read(self, _bytes=1):
        self.__delay()
        with self.lock:
            return self.smu.read(_bytes)

    def query(self, cmd):
        self.write(cmd)
        with self.lock:
            _data = self.smu.read_until(self.read_termination_b)
            _c = self.smu.read()
            while _c:
                _data += _c
                _c = self.smu.read()
            self.__writebuffer(cmd, _data)
        try:
            logger.debug(f'<-> {self.buffer[-1]}')
        except IndexError:
            logger.debug(f'{cmd} failed to return result')
        return self.lastreading

    def get_wait_for_meas(self):
        self.write('*OPC?')
        return OPCThread(self.smu, self.lock)

    def get_reader(self):
        return READThread(self.smu, self.lock,
                          self.read_termination_b,
                          self.write_termination_b)


class OPCThread(threading.Thread):

    def __init__(self, smu, lock):
        super().__init__()
        self.smu = smu
        self.lock = lock
        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        starttime = time.time()
        while self.alive.is_set():
            with self.lock:
                _s = self.smu.read(1)
            if _s == b'1':
                logger.debug("OPCThread completed.")
                self.alive.clear()
                break
            elif time.time() - starttime > 300:
                logger.warning("OPCThread timeout reached.")
                self.alive.clear()
                break
            time.sleep(1)

    def kill(self):
        self.alive.clear()

    @property
    def active(self):
        return self.alive.is_set()

    @property
    def alive_event(self):
        return self.alive

class READThread(threading.Thread):

    def __init__(self, smu, lock, read_termination, write_termination):
        super().__init__()
        self.smu = smu
        self.lock = lock
        self.alive = threading.Event()
        self.alive.set()
        self.read_termination = read_termination
        self.write_termination = write_termination

    def run(self):
        while self.alive.is_set():
            time.sleep(0.1)

    def kill(self):
        self.alive.clear()

    @property
    def active(self):
        return self.alive.is_set()

    @property
    def alive_event(self):
        return self.alive

    def read(self):
        if self.alive.is_set():
            with self.lock:
                self.smu.write(b':READ?'+self.write_termination)
                time.sleep(0.1)
                logger.debug(">>:READ?")
                i = 0
                _data = b''
                while not _data and i < 3:
                    _data = self.smu.read_until(self.read_termination)
                    time.sleep(1)
                    i += 1
            return _data.strip()
        else:
            return b''

# def initialize_gpib(address, board, query_id=True, read_termination="LF", **kwargs):
#     """ Initalize GPIB devices using PyVisa """
#
#     gpib_name = f"GPIB{board}::{address}::INSTR"
#     try:
#         gpib_visa = rm.open_resource(gpib_name)
#         if read_termination == "LF":
#             gpib_visa.read_termination = "\n"
#             gpib_visa.write_termination = "\n"
#         elif read_termination == "CR":
#             gpib_visa.read_termination = "\r"
#             gpib_visa.write_termination = "\r"
#         elif read_termination == "CRLF":
#             gpib_visa.read_termination = "\r\n"
#             gpib_visa.write_termination = "\r\n"
#         for kw in list(kwargs.keys()):
#             tmp = "".join(("gpib_visa.", kw, "=", kwargs[kw]))
#             exec(tmp)
#         if query_id:
#             print(gpib_visa.query("*IDN?"))
#     except Exception:
#         print("Failed opening GPIB address %d\n" % address)
#         gpib_visa = None
#     return gpib_visa
#
#
# def initialize_serial_pyvisa(name, idn="*IDN?", read_termination="LF", **kwargs):
#     """ Initialize Serial devices using PyVisa """
#
#     try:
#         print(f"Opening {name}")
#         serial_visa = rm.open_resource(name)
#         print("Setting timeout")
#         serial_visa.timeout = 5000  # 5s
#         print("Setting read_termination")
#         if read_termination == "LF":
#             serial_visa.read_termination = "\n"
#         elif read_termination == "CR":
#             serial_visa.read_termination = "\r"
#         elif read_termination == "CRLF":
#             serial_visa.read_termination = "\r\n"
#         for kw in list(kwargs.keys()):
#             tmp = "".join(("serial_visa.", kw, "=", kwargs[kw]))
#             exec(tmp)
#         print(f"Sending {idn}")
#         print(serial_visa.query(idn))
#     except Exception:
#         print("Failed opening serial port %s\n" % name)
#         serial_visa = None
#     return serial_visa