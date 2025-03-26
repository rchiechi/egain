import os
import sys
import glob
import time
import json
import serial
import egain.thermo.constants as tc

def enumerateDevices(**kwargs):
    _first = kwargs.get("first", None)
    if sys.platform.startswith("darwin"):
        _filters = ['usbmodem']
    if sys.platform.startswith("linux"):
        _filters = ['serial0', 'serial1', 'ttyACM', 'ttyUSB']
    _devs = set()
    try:
        for _dev in os.listdir('/dev'):
            for _filter in _filters:
                if _filter.lower() in _dev.lower():
                    _devs.add(os.path.join('/', 'dev', _dev))
    except FileNotFoundError:
        _devs = serial_ports()
    if _first is None:
        device_list = list(_devs)
    else:
        device_list = []
        for _dev in _devs:
            if _first in _dev:
                device_list.append(_dev)
        for _dev in _devs:
            if _first not in _dev:
                device_list.append(_dev)
    return (device_list)

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
        _ports += glob.glob("/dev/serial*")
    else:
        raise EnvironmentError("Unsupported platform")

    ports = set()
    for _port in _ports:
        try:
            s = serial.Serial(_port)
            s.close()
            ports.add(_port)
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