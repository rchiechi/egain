import os
import json
import time
import logging
import threading
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

    is_initialized = False
    temps = {'upper':0, 'lower':0, 'target': 25}

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.controller = None
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

        self.peltierCheck = tk.Checkbutton(setFrame,
                                           text='Enable',
                                           variable=self.peltier_on,
                                           state=DISABLED,
                                           command=self._setPeltier)

        peltierPower = tk.Label(master=setFrame,
                                textvariable=self.peltierPowerString,
                                width=8)
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
                                     *enumerateDevices(first='ttyACM0'))
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
        self.targettemp.set('25')

    def shutdown(self):
        try:
            self.controller.kill()
        except AttributeError:
            pass

    def _setPeltier(self):
        if self.peltier_on.get():
            cmd = 'ON'
        else:
            cmd = 'OFF'
        self.controller.sendcmd(cmd)

    def _checkPeltier(self):
        self.peltierCheck.after(1000, self._checkPeltier)
        _state = self.controller.status.get('Peltier_on', None)
        if _state:
            self.peltier_on.set(1)
        else:
            self.peltier_on.set(0)
        _mode = self.controller.status.get("MODE", '?').lower()
        if self.modeButton["text"].lower() != _mode.lower():
            self.modeButton["text"] = _mode.title()

    def _setMode(self):
        _mode = self.modeButton["text"].lower()
        if _mode != 'heat':
            self.controller.sendcmd('HEAT')
        elif _mode != 'cool':
            self.controller.sendcmd('COOL')

    def _setTemp(self):
        if not self.targettemp.get():
            return False
        try:
            _temp = int(self.targettemp.get())
            if -100 < _temp < 100:
                return True
        except ValueError:
            pass
        self.targettemp.set('25')
        return True

    def _readTemps(self):
        self.tempFrame.after(250, self._readTemps)
        _temps = self.controller.status
        self.temps['upper'] = _temps.get('UPPER', -999.9)
        self.temps['lower'] = _temps.get('LOWER', -999.9)
        self.temps['target'] = _temps.get('TARGET', 25)
        self.upperTempString.set('Upper: %0.2f °C' % self.temps['upper'])
        self.lowerTempString.set('Lower: %0.2f °C' % self.temps['lower'])
        if self._setTemp() and self.temps['target'] != int(self.targettemp.get()):
            logger.info(f"Setting peltier to {self.targettemp.get()} °C")
            self.controller.sendcmd('SETTEMP', self.targettemp.get())
        power = self.controller.status.get('Power', 0)
        self.peltierPowerString.set(f'Power: {power}')

    def _initdevice(self, *args):
        if self.device.get() == DEFAULTUSBDEVICE:
            return
        logger.info("Initializing device.")
        ser_port = os.path.join('/', 'dev', self.device.get())
        if not os.path.exists(ser_port):
            return
        self.controller = SerialReader(serial.Serial(ser_port, 9600, timeout=0.5, write_timeout=1))
        self.controller.start()
        n = 0
        while not self.controller.initialized:
            time.sleep(1)
            n += 1
            if n > 9:
                logger.warning("Device initialization failed.")
                return
        logger.info("Device initalized")
        self.is_initialized = True
        self.modeButton['state'] = NORMAL
        self.peltierCheck['state'] = NORMAL
        self._readTemps()
        self._checkPeltier()


class SerialReader(threading.Thread):

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.alive = threading.Event()
        self.alive.set()
        self.is_initialized = False
        self.lock = threading.Lock()
        self.last_update = time.time()
        self.msg = {}
        self.cmds = []

    def run(self):
        logger.debug("SerialReader connecting")
        self._initdevice()
        while self.isalive and self.initialized:
            while len(self.cmds):
                self._writeserial(*self.cmds.pop())
                time.sleep(0.1)
            self._pollserial()
            time.sleep(0.25)
        logger.debug("SerialReader ended")

    def sendcmd(self, cmd, val=None):
        self.cmds.append([cmd, val])

    def _initdevice(self):
        try:
            n = 0
            _json = ''
            while not self.is_initialized or n < 10:
                _json = str(self.controller.readline(), encoding='utf8')
                logger.debug("SerialReadergot init: %s",n, _json)
                try:
                    self.msg = json.loads(_json)
                    _val = self.msg.get('message', '')
                    if _val == 'Done initializing':
                        logger.debug("SerialReader initalized")
                        self.is_initialized = True
                        break
                except json.decoder.JSONDecodeError:
                    pass
                self._pollserial()
                self.is_initialized = bool(self.status.get('INITIALIZED', 0))
                logger.debug("SerialReader got json: %s", self.status)
                n += 1
        except serial.serialutil.SerialException:
            logger.error("SerialReader could not communicate with Serial device.")
        except AttributeError:
            logger.error("SerialReader was passed bad Serial device.")

    def _pollserial(self):
        try:
            self._writeserial('POLL')
            with self.lock:
                _json = str(self.controller.readline(), encoding='utf8').strip()
            try:
                self.msg = json.loads(_json)
                self.last_update = time.time()
            except json.decoder.JSONDecodeError as err:
                logger.debug(f'SerialReader JSON Error: {err}')
        except serial.serialutil.SerialException:
            logger.error(f"Error reading from {self.controller.name}.")

    def _writeserial(self, cmd, val=None):
        try:
            with self.lock:
                if cmd != "POLL":
                    logger.debug("SerialReader sending %s: %s", cmd, val)
                self.controller.write(bytes(cmd, encoding='utf8')+b';')
                if val is not None:
                    self.controller.write(bytes(val, encoding='utf8'))
        except serial.serialutil.SerialException:
            logger.error(f"Error sending command to {self.controller.name}.")

    def kill(self):
        logger.debug("SerialReader thread dying")
        self.alive.clear()
        try:
            if self.is_initialized:
                self._writeserial("OFF")
        except AttributeError:
            pass

    @property
    def age(self):
        return time.time() - self.last_serial

    @property
    def isalive(self):
        return self.alive.is_set()

    @property
    def initialized(self):
        return self.is_initialized

    @property
    def status(self):
        return self.msg


if __name__ == '__main__':
    root = Tk()
    main = TempControl(root)
    main.pack()
    root.mainloop()
