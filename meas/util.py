import os
import sys
import glob
import serial

def enumerateDevices(**kwargs):
    _first = kwargs.get("first", None)
    _filter = ''
    if sys.platform.startswith("darwin"):
        _filters = ['usbmodem']
    if sys.platform.startswith("linux"):
        _filters = ['ttyACM', 'ttyUSB']
    if _first is not None:
        _devs = [_first]
    else:
        _devs = []
    try:
        for _dev in os.listdir('/dev'):
            for _filter in _filters:
                if _filter.lower() in _dev.lower():
                    _devs.append(os.path.join('/', 'dev', _dev))
    except FileNotFoundError:
        _devs = serial_ports()
    return _devs

def serial_ports(**kwargs):
    """
    Enumerates all serial devices on the system.

    Returns:
    A list of serial device paths.
    """
    _first = kwargs.get("first", None)
    _ports = [_first] if _first is not None else []
    if os.name == "nt":
        _ports += [f"COM{i}" for i in range(256)]
    elif os.name == "posix":
        _ports += glob.glob("/dev/tty[A-Za-z]*")
    else:
        raise EnvironmentError("Unsupported platform")

    ports = []
    for _port in _ports:
        try:
            s = serial.Serial(_port)
            s.close()
            ports.append(_port)
        except (OSError, serial.SerialException):
            pass
    return ports
