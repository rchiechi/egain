import os
import sys
import glob
import serial

def enumerateDevices(_first=None):
    _filter = ''
    if sys.platform.startswith("darwin"):
        _filter = 'usbmodem'
    if sys.platform.startswith("linux"):
        _filter = 'ttyACM'
    if _first is not None:
        _devs = [_first]
    else:
        _devs = []
    try:
        for _dev in os.listdir('/dev'):
            if _filter.lower() in _dev.lower():
                _devs.append(os.path.join('/', 'dev', _dev))
    except FileNotFoundError:
        _devs = serial_ports()
    return _devs

def serial_ports(_first=None):
    """
    Enumerates all serial devices on the system.

    Returns:
    A list of serial device paths.
    """
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
