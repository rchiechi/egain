import os
import json
import time
import logging
import tkinter.ttk as tk
from tkinter import Tk
from tkinter import IntVar, StringVar
from tkinter import N, X
from tkinter import TOP, BOTTOM, LEFT, RIGHT, DISABLED, NORMAL
import serial
from meas.util import enumerateDevices

TEMPS = {'UPPER':None, 'LOWER':None}
DEFAULTUSBDEVICE = 'Choose USB Device'

logger = logging.getLogger(__package__+'.peltier')

class TempControl(tk.Frame):

    controller = None
    is_initialized = False
    temps = {'upper':0, 'lower':0}

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.upperTempString = StringVar()
        self.lowerTempString = StringVar()
        self.peltierPowerString = StringVar()
        self.device = StringVar()
        self.targettemp = StringVar()
        self.peltier_on = IntVar()
        self.last_serial = 0
        self.createWidgets()

    def __setitem__(self, what, value):
        if what == 'state':
            if value == DISABLED:
                self.is_initialized = False
        else:
            self.configure(**{what:value})

    @property
    def initialized(self):
        return self.is_initialized

    @property
    def uppertemp(self):
        return self.temps['upper']

    @property
    def lowertemp(self):
        return self.temps['lower']

    @property
    def peltierstatus(self):
        return bool(self.peltier_on.get())

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
        self.peltierCheck.after(100, self._checkPeltier)

        peltierPower = tk.Label(master=setFrame,
                                textvariable=self.peltierPowerString,
                                width=4)
        modeFrame = tk.LabelFrame(self,
                                  text='Peltier Mode',
                                  labelanchor=N)
        self.modeButton = tk.Button(master=modeFrame,
                                    text='Off',
                                    command=self._setMode,
                                    state=DISABLED)

        devicePicker = tk.OptionMenu(self,
                                     self.device,
                                     DEFAULTUSBDEVICE,
                                     *enumerateDevices())
        self.device.trace_add('write', self._initdevice)

        setTemp.pack(side=LEFT)
        peltierPower.pack(side=LEFT)
        self.peltierCheck.pack(side=RIGHT)
        self.modeButton.pack(side=TOP)
        devicePicker.pack()
        upperTemp.pack(side=TOP, expand=False)
        lowerTemp.pack(side=BOTTOM)
        setFrame.pack(side=TOP)
        modeFrame.pack(side=TOP, fill=X)
        self.tempFrame.pack(side=TOP)
        # self.pack()
        self._readTemps()

    def shutdown(self):
        self.writeserial('OFF')

    def _setPeltier(self):
        if self.peltier_on.get():
            cmd = 'ON'
        else:
            cmd = 'OFF'
        self.writeserial(cmd)

    def _checkPeltier(self):
        self.peltierCheck.after('1000', self._checkPeltier)
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
        _mode = self.readserial().get("MODE", '?').title()
        if self.modeButton["text"] != _mode:
            self.modeButton["text"] = _mode.title()

    def _setMode(self):
        _mode = self.modeButton["text"].lower()
        if _mode != 'heat':
            self.writeserial('HEAT')
        elif _mode != 'cool':
            self.writeserial('COOL')

    def _setTemp(self, *args):
        logger.info(f"Setting peltier to {self.targettemp.get()} °C")
        self.writeserial('SETTEMP', self.targettemp.get())

    def _readTemps(self):
        self.tempFrame.after('500', self._readTemps)
        _temps = self.readserial()
        self.temps['upper'] = _temps.get('UPPER', -999.9)
        self.temps['lower'] = _temps.get('LOWER', -999.9)
        if self.temps['upper'] > -1000:
            self.upperTempString.set('Upper: %0.2f °C' % self.temps['upper'])
        if self.temps['lower'] > -1000:
            self.lowerTempString.set('Lower: %0.2f °C' % self.temps['lower'])

    def _initdevice(self, *args):
        if self.device.get() == DEFAULTUSBDEVICE:
            return
        logger.info("Initializing device.")
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
                        logger.info("Device initalized")
                        self.is_initialized = True
                        self.modeButton['state'] == NORMAL
                        return
                except json.decoder.JSONDecodeError:
                    continue
                n += 1
        except serial.serialutil.SerialException:
            return
        logger.warning("Empty reply from device.")

    def readserial(self):
        if not self.is_initialized:
            return {}
        try:
            _json = ''
            while not _json:
                self.writeserial('POLL')
                _json = str(self.controller.readline(), encoding='utf8').strip()
                try:
                    msg = json.loads(_json)
                    if 'message' in msg:
                        logger.debug(msg)
                        self.is_initialized = False
                    return msg
                except json.decoder.JSONDecodeError as err:
                    logger.warning(f'JSON Error: {err}')
        except serial.serialutil.SerialException:
            pass
        logger.error(f"Error reading from {self.controller.name}.")
        return {}

    def writeserial(self, cmd, val=None):
        if not self.is_initialized:
            return
        if not cmd:
            return
        if time.time() - self.last_serial < 0.5:
            time.sleep(0.5)
        try:
            self.controller.write(bytes(cmd, encoding='utf8')+b';')
            # print(f"Wrote {cmd};", end="")
            if val is not None:
                self.controller.write(bytes(val, encoding='utf8'))
                logger.debug(f"{val}", end="")
            # print(f" to {self.controller.name}.")
        except serial.serialutil.SerialException:
            logger.error(f"Error sending command to {self.controller.name}.")
        self.last_serial = time.time()


if __name__ == '__main__':
    root = Tk()
    main = TempControl(root)
    main.pack()
    root.mainloop()
