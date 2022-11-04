import os
import json
import platform
import time
import tkinter.ttk as tk
from tkinter import Tk
from tkinter import Text, IntVar, StringVar, Listbox, Label, Entry
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
# from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
import serial

TEMPS = {'UPPER':None, 'LOWER':None}
DEFAULTUSBDEVICE = 'Choose USB Device'

class TempControl(tk.Frame):

    controller = None
    initialized = False

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.upperTempString = StringVar()
        self.lowerTempString = StringVar()
        self.peltierPowerString = StringVar()
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

        setTemp = tk.Entry(setFrame, textvariable=self.targettemp, width=4)
        self.targettemp.trace('w', self._setTemp)

        self.peltierCheck = tk.Checkbutton(setFrame,
                                           text='Peliter On',
                                           variable=self.peltier_on,
                                           command=self._setPeltier)

        peltierPower = tk.Label(master=setFrame,
                                textvariable=self.peltierPowerString,
                                width=4)

        self.peltierCheck.after(100, self._checkPeltier)

        devicePicker = tk.OptionMenu(self,
                                     self.device,
                                     DEFAULTUSBDEVICE,
                                     *_enumerateDevices())
        self.device.trace_add('write', self._initdevice)

        setTemp.pack(side=LEFT)
        peltierPower.pack(side=LEFT)
        self.peltierCheck.pack(side=RIGHT)
        devicePicker.pack()
        upperTemp.pack(side=TOP, expand=False)
        lowerTemp.pack(side=BOTTOM)
        setFrame.pack(side=TOP)
        self.tempFrame.pack(side=TOP)
        # self.pack()
        self._readTemps()

    def _setPeltier(self):
        if self.peltier_on.get():
            cmd = 'ON'
        else:
            cmd = 'OFF'
        if self.initialized:
            self.writeserial(cmd)

    def _checkPeltier(self):
        self.peltierCheck.after('2000', self._checkPeltier)
        _msg = self.readserial()
        power = _msg.get('Power', 0)
        self.peltierPowerString.set(str(power))
        _state = _msg.get('Peltier_on', None)
        if _state is None:
            self.peltierCheck.configure(state='disabled')
            return
        self.peltierCheck.configure(state='normal')
        if _state:
            self.peltier_on.set(1)
        else:
            self.peltier_on.set(0)

    def _setTemp(self, *args):
        print(f"Setting {self.controller.name} to {self.targettemp.get()} °C")
        self.writeserial('SETTEMP', self.targettemp.get())

    def _readTemps(self):
        self.tempFrame.after('500', self._readTemps)
        _temps = self.readserial()
        upper = _temps.get('UPPER', -999.9)
        lower = _temps.get('LOWER', -999.9)
        if upper != -999.9:
            self.upperTempString.set('Upper: %0.2f °C' % upper)
        if lower != -999.0:
            self.lowerTempString.set('Lower: %0.2f °C' % lower)

    def _initdevice(self, *args):
        if self.device.get() == DEFAULTUSBDEVICE:
            return
        print("Initializing device.")
        n = 0
        ser_port = os.path.join('/', 'dev', self.device.get())
        if not os.path.exists(ser_port):
            return
        try:
            self.controller = serial.Serial(ser_port, 9600, timeout=0.5)
            time.sleep(1)
            _json = ''
            while not _json or n < 10:
                _json = str(self.controller.readline(), encoding='utf8')
                try:
                    _msg = json.loads(_json)
                    _val = _msg.get('message', '')
                    if _val == 'Done initializing':
                        print("Device initalized")
                        self.initialized = True
                        return
                except json.decoder.JSONDecodeError:
                    continue
                n += 1
        except serial.serialutil.SerialException:
            return
        print("Empty reply from device.")

    def readserial(self):
        if not self.initialized:
            return {}
        try:
            _json = ''
            while not _json:
                self.writeserial('POLL')
                _json = str(self.controller.readline(), encoding='utf8').strip()
                try:
                    msg = json.loads(_json)
                    # print(msg)
                    if 'message' in msg:
                        print(msg)
                        self.initialized = False
                    return msg
                except json.decoder.JSONDecodeError as err:
                    print(f'JSON Error: {err}')
        except serial.serialutil.SerialException:
            pass
        print(f"Error reading from {self.controller.name}.")
        return {}

    def writeserial(self, cmd, val=None):
        if not self.initialized:
            return
        if not cmd:
            return
        try:
            self.controller.write(bytes(cmd, encoding='utf8')+b';')
            print(f"Wrote {cmd};", end="")
            if val is not None:
                self.controller.write(bytes(val, encoding='utf8'))
                print(f"{val}", end="")
            print(f" to {self.controller.name}.")
        except serial.serialutil.SerialException:
            print(f"Error sending command to {self.controller.name}.")

def _enumerateDevices():
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    if platform.system() == "Linux":
        _filter = 'ttyACM'
    _devs = []
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    # _devs.append(DEFAULTUSBDEVICE)
    return _devs


if __name__ == '__main__':
    root = Tk()
    main = TempControl(root)
    main.pack()
    root.mainloop()
