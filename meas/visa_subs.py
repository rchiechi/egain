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
from contextlib import contextmanager
import pyvisa as visa
rm = visa.ResourceManager()


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


def initialize_serial(name, idn="*IDN?", read_termination="LF", **kwargs):
    """ Initialize Serial devices using PyVisa """

    try:
        serial_visa = rm.open_resource(name)
        if read_termination == "LF":
            serial_visa.read_termination = "\n"
        elif read_termination == "CR":
            serial_visa.read_termination = "\r"
        elif read_termination == "CRLF":
            serial_visa.read_termination = "\r\n"
        for kw in list(kwargs.keys()):
            tmp = "".join(("serial_visa.", kw, "=", kwargs[kw]))
            exec(tmp)
        print(serial_visa.query(idn))
    except Exception:
        print("Failed opening serial port %s\n" % name)
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
    # _filter = ''
    # if platform.system() == "Darwin":
    #     _filter = 'usbmodem'
    # if platform.system() == "Linux":
    #     _filter = 'ttyACM'
    _devs = []
    rm = visa.ResourceManager('@py')
    with _mutestderr():
        for _dev in rm.list_resources():
            # if _filter.lower() in _dev.lower():
            _devs.append(_dev)
        # _devs.append(DEFAULTUSBDEVICE)
    return _devs