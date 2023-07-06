import os
import sys
import glob
import time
import json
import serial
import thermo.constants as tc

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

def init_thermo_device(device):
    print(f"\nInitializing {device}...", end='')
    n = 0
    try:
        ser_port = os.path.join('/', 'dev', device)
        thermo = serial.Serial(ser_port, 115200, timeout=1)
        _json = ''
        while not _json or n < 10:
            time.sleep(1)
            _json = str(thermo.readline(), encoding='utf8')
            try:
                _msg = json.loads(_json)
                _val = _msg.get('message', '')
                if _val == tc.INITIALIZED:
                    print("\nDevice initalized")
                    time.sleep(0.5)
                    thermo.write(tc.SHOWSTATUS+tc.TERMINATOR)
                    time.sleep(0.5)
                    print("Done!")
                    return thermo
                else:
                    print(_val)
            except json.decoder.JSONDecodeError:
                print(f"{n}...", end='')
                sys.stdout.flush()
            n += 1
    except serial.serialutil.SerialException:
        return None
    print("\nEmpty reply from device.")
    return None