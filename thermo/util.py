import os
import sys
import time
import json
import serial
import thermo.constants as tc

def enumerateDevices(_first=None):
    _filter = ''
    if sys.platform == "darwin":
        _filter = 'usbmodem'
    if sys.platform == "linux":
        _filter = 'ttyACM'
    if _first is not None:
        _devs = [_first]
    else:
        _devs = []
    try:
        for _dev in os.listdir('/dev'):
            if _filter.lower() in _dev.lower():
                _devs.append(_dev)
    except FileNotFoundError:
        pass
    return _devs

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