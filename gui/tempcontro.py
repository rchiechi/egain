import os
import json
import platform
# import asyncio
# import logging
# import threading
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, Listbox, Label, Entry
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
import serial

TEMPS = {'UPPER':None, 'LOWER':None}

class TempControl(tk.Frame):

    controller = None

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.upperTempString = StringVar()
        self.lowerTempString = StringVar()
        self.device = StringVar()
        self.targettemp = StringVar()
        self.peltier_on = IntVar()
        self.createWidgets()

    def createWidgets(self):
        setFrame = tk.LabelFrame(self,
                                 text='Target Temperature (°C)',
                                 labelanchor=N)
        self.tempFrame = tk.LabelFrame(self,
                                       text='Current Temperatures (°C)',
                                       labelanchor=N)
        upperTemp = tk.Label(master=self.tempFrame,
                             textvariable=self.upperTempString)
        lowerTemp = tk.Label(master=self.tempFrame,
                             textvariable=self.lowerTempString)

        setTemp = tk.Entry(setFrame, textvariable=self.targettemp)
        self.targettemp.trace('w', self._setTemp)

        self.peltierCheck = tk.Checkbutton(setFrame,
                                           text='Peliter On',
                                           variable=self.peltier_on,
                                           command=self._setPeltier)
        self.peltierCheck.after(100, self._checkPeltier)

        devicePicker = tk.OptionMenu(self, self.device, *_enumerateDevices())
        self.device.trace('w', self._initdevice)

        setTemp.pack(side=LEFT)
        self.peltierCheck.pack(side=RIGHT)
        devicePicker.pack()
        upperTemp.pack(side=TOP, expand=False)
        lowerTemp.pack(side=BOTTOM)
        setFrame.pack(side=TOP)
        self.tempFrame.pack(side=TOP)
        self.pack()
        self._initdevice(None)
        self._readTemps()

    def _setPeltier(self):
        if self.peltier_on.get():
            cmd = 'ON'
        else:
            cmd = 'OFF'
        writeserial(self.controller, cmd)

    def _checkPeltier(self):
        self.peltierCheck.after(500, self._checkPeltier)
        _msg = readserial(self.controller)
        _state = _msg.get('Peltier_on', None)
        if _state is None:
            print("Error fetching Peliter state.")
            return
        if _state:
            self.peltier_on.set(1)
        self.peltier_on.set(0)

    def _setTemp(self, *args):
        # self._initdevice()
        print(f"Setting {self.controller.name} to {self.targettemp.get()} °C")
        writeserial(self.controller, 'SETTEMP', self.targettemp.get())

    def _initdevice(self, *args):
        ser_port = os.path.join('/', 'dev', self.device.get())
        if not os.path.exists(ser_port):
            return
        try:
            self.controller = serial.Serial(ser_port, 9600, timeout=0.5)
            self.controller.readline()
            _json = ''
            # while not _json:
            _json = str(self.controller.readline(), encoding='utf8')
            print(f'_init json: {_json}')
            try:
                _msg = json.loads(_json)
                _val = _msg.get('message', '')
                print(f'_val:{_val}')
                if _val == 'Done initializing':
                    print("Device initalized")
                    # break
            except json.decoder.JSONDecodeError:
                print("Empty reply from device.")
                # continue
        except serial.serialutil.SerialException:
            return

    def _readTemps(self):
        self.tempFrame.after('500', self._readTemps)
        # print(f"Reading temps from {self.controller.name}")
        _temps = readserial(self.controller)
        upper = _temps.get('UPPER', None)
        lower = _temps.get('LOWER', None)
        if None in (upper, lower):
            print("Error reading temperatures.")
        self.upperTempString.set(f'Upper: {str(upper)} °C')
        self.lowerTempString.set(f'Lower: {str(lower)} °C')

def _enumerateDevices():
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    _devs = []
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    return _devs

# def peltierset(ser, enabled):
#     try:
#         if enabled:
#             ser.write(b'ON;')
#             print('Setting peltier ON')
#         else:
#             ser.write(b'OFF;')
#             print('Setting peltier OFF')
#     except serial.serialutil.SerialException:
#         print("Error setting peltier status")
# 
# def peltiercheck(ser):
#     peltier = None
#     try:
#         ser.write(b'CHECK;')
#         _json = ''
#         while True:
#             _json = str(ser.readline(), encoding='utf8')
#             print(f'peltier json: {_json}')
#             try:
#                 peltier = json.loads(_json).get('Peliter_on', None)
#                 break
#             except json.decoder.JSONDecodeError:
#                 break
#     except serial.serialutil.SerialException:
#         print("Error reading peltier status")
#     return(peltier)
# 
# def settemp(ser, temp):
#     if not temp:
#         return
#     try:
#         ser.write(b'SETTEMP;{temp}')
#         print(f"Wrote to {ser.name}.")
#     except serial.serialutil.SerialException:
#         print("Error setting temp.")
# 
# 
# def readtemps(ser):
#     temps = TEMPS
#     try:
#         ser.write(b'GETTEMP;')
#         _json = ''
#         while True:
#             _json = str(ser.readline(), encoding='utf8')
#             print(f'_temp json: {_json}')
#             try:
#                 temps = json.loads(_json)
#                 if 'UPPER' in temps or 'LOWER' in temps:
#                     print(temps)
#                     break
#             except json.decoder.JSONDecodeError:
#                 break
#     except serial.serialutil.SerialException:
#         print("Error reading temps")
#         return TEMPS
#     return(temps)

def readserial(ser):
    if ser is None:
        return {}
    _chrs = []
    try:
        while True:
            _chrs.append(ser.read(1))
            # print(str(b''.join(_chrs), encoding='utf8'), end='')
            if _chrs[-1] not in (b'\n', b'}'):
                continue
            if _chrs == [b'\r', b'\n']:
                _chrs = []
                continue
            _json = str(b''.join(_chrs), encoding='utf8')
            # print(f'_json: {_json};')
            try:
                return json.loads(_json)
            except json.decoder.JSONDecodeError as err:
                print(f'JSON Error: {err}')
                break
    except serial.serialutil.SerialException:
        pass
    print(f"Error reading from {ser.name}.")
    return {}

def writeserial(ser, cmd, val=None):
    if ser is None:
        return
    if not cmd:
        return
    try:
        ser.write(b'{cmd};')
        print(f"Wrote {cmd};", end="")
        if val is not None:
            ser.write(b'{val}')
            print(f"{val}", end="")
        print(f" to {ser.name}.")
    except serial.serialutil.SerialException:
        print(f"Error sending command to {ser.name}.")


if __name__ == '__main__':
    root = Tk()
    main = TempControl(root)
    root.mainloop()
