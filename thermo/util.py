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
                _devs.append(_dev)
    except FileNotFoundError:
        _devs = serial_ports()
    return _devs

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    # https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

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