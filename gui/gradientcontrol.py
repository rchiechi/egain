import os
import json
import platform
import time
import subprocess
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
from multiprocessing.connection import Client, Listener
import thermo.constants as tc

TEMPS = {'LEFT':None, 'RIGHT':None}
DEFAULTUSBDEVICE = 'Choose USB Device'


class Meas(tk.Frame):

    _lt = 0.0
    _rt = 0.0
    _initialized = False
    last_status = {}
    widgets = {}
    _host = '127.0.0.1'
    _port = '6000'

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.addr = StringVar(value=f'{self._host}:{self._port}')
        self.createWidgets()
        self.readstatus()

    def createWidgets(self):
        return

    def _checkconnetion(self):
        if not ping(self.host):
            self._initalized = False
            return False
        try:
            with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
                client.send(tc.COMMAND_STAT)
                msg = client.recv()
                if not isinstance(msg, dict):
                    msg = {}
            if msg.get('status', tc.STAT_ERROR) == tc.STAT_OK:
                self._initalized = True
                return True
        except ConnectionRefusedError:
            print(f"Host {self.addr.get().strip()} is down.")
        self._initalized = False
        return False

    def readstatus(self, *args):
        if not self.connected:
            self.after(5000, self.readstatus)
            return
        with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
            client.send(tc.COMMAND_READ)
            msg = client.recv()
            if not isinstance(msg, dict):
                msg = {}
        self.after(1000, self.readstatus)
        self.last_status = msg

    def sendcommand(self, cmd, val=None):
        if not self.connected:
            return
        with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
            client.send(tc.COMMAND_SEND)
            client.send([cmd, val])

    @property
    def host(self):
        try:
            _addr, _port = self.addr.get().strip().split(':')
            if validateip(_addr):
                return _addr
        except ValueError:
            pass
        return None

    @property
    def port(self):
        try:
            _addr, _port = self.addr.get().strip().split(':')
            return int(_port)
        except ValueError:
            return None

    @property
    def connected(self):
        return self._checkconnetion()

    @property
    def initialized(self):
        return self._initialized


class TempControl(Meas):

    _port = tc.PELTIER_PORT

    def createWidgets(self):
        self.leftTempString = StringVar()
        self.rightTempString = StringVar()
        self.leftPeltierPowerString = StringVar()
        self.rightPeltierPowerString = StringVar()
        self.device = StringVar()
        self.lefttargettemp = StringVar()
        self.righttargettemp = StringVar()
        self.left_peltier_on = IntVar()
        self.right_peltier_on = IntVar()

        self.tempFrame = tk.LabelFrame(self,
                                       text='Current Temperatures (°C)',
                                       labelanchor=N)
        leftTemp = tk.Label(master=self.tempFrame,
                            textvariable=self.leftTempString)
        rightTemp = tk.Label(master=self.tempFrame,
                             textvariable=self.rightTempString)
        setFrame = tk.LabelFrame(self,
                                 text='Target Temperatures (°C)',
                                 labelanchor=N)
        tc.SETLEFTTEMP = tk.Entry(setFrame, textvariable=self.lefttargettemp, width=4)
        tc.SETRIGHTTEMP = tk.Entry(setFrame, textvariable=self.righttargettemp, width=4)
        self.lefttargettemp.set("25.0")
        self.righttargettemp.set("25.0")
        for n in ('<Return>', '<Leave>', '<Enter>'):
            tc.SETLEFTTEMP.bind(n, self._setTemp)
            tc.SETRIGHTTEMP.bind(n, self._setTemp)
        # self.lefttargettemp.trace('w', self._setTemp)
        # self.righttargettemp.trace('w', self._setTemp)
        toggleFrame = tk.Frame(self)
        peltierLeftCheck = tk.Checkbutton(toggleFrame,
                                          text='Left Peliter On',
                                          variable=self.left_peltier_on,
                                          command=lambda: self._setPeltier('LEFT'))
        peltierRightCheck = tk.Checkbutton(toggleFrame,
                                           text='Right Peliter On',
                                           variable=self.right_peltier_on,
                                           command=lambda: self._setPeltier('RIGHT'))
        self.widgets['peltierLeftCheck'] = peltierLeftCheck
        self.widgets['peltierRightCheck'] = peltierRightCheck
        heatcoolFrame = tk.Frame(self)
        leftheatcoolButton = tk.Button(heatcoolFrame, text="Heat",
                                       command=lambda: self._heatcoolbuttonclick('leftheatcoolButton'),
                                       width=5)
        rigthheatcoolButton = tk.Button(heatcoolFrame, text="Cool",
                                        command=lambda: self._heatcoolbuttonclick('rigthheatcoolButton'),
                                        width=5)
        self.widgets['leftheatcoolButton'] = leftheatcoolButton
        self.widgets['rightheatcoolButton'] = rigthheatcoolButton

        leftPeltierPower = tk.Label(master=setFrame,
                                    textvariable=self.leftPeltierPowerString,
                                    width=4)

        rightPeltierPower = tk.Label(master=setFrame,
                                     textvariable=self.rightPeltierPowerString,
                                     width=4)

        deviceFrame = tk.LabelFrame(self,
                                    text='Device Settings',
                                    labelanchor=N)
        tk.Label(deviceFrame,
                 text='Address:').pack(side=LEFT)
        tk.Entry(deviceFrame,
                 width=15,
                 textvariable=self.addr).pack(side=LEFT)

        tc.SETLEFTTEMP.pack(side=LEFT)
        leftPeltierPower.pack(side=LEFT)
        tc.SETRIGHTTEMP.pack(side=LEFT)
        rightPeltierPower.pack(side=LEFT)
        peltierRightCheck.pack(side=RIGHT)
        peltierLeftCheck.pack(side=RIGHT)
        leftTemp.pack(side=TOP, expand=False)
        rightTemp.pack(side=BOTTOM)
        leftheatcoolButton.pack(side=LEFT)
        rigthheatcoolButton.pack(side=LEFT)
        toggleFrame.pack(side=TOP)
        heatcoolFrame.pack(side=TOP)
        setFrame.pack(side=TOP)
        self.tempFrame.pack(side=TOP)
        deviceFrame.pack(side=TOP)

        for _widget in self.widgets:
            self.widgets[_widget].configure(state=DISABLED)
        self._readTemps()
        self._checkPeltier()

    def shutdown(self):
        self.sendcommand(tc.LEFTOFF)
        self.sendcommand(tc.RIGHTOFF)

    def _setPeltier(self, side):
        if getattr(self, f'{side.lower()}_peltier_on').get():
            cmd = f'{side.upper()}ON'
        else:
            cmd = f'{side.upper()}OFF'
        if self.initialized:
            self.sendcommand(cmd)

    def _checkPeltier(self, *args):
        self.after('1000', self._checkPeltier)
        print(self.last_status)
        if not self.initialized:
            return
        for _widget in self.widgets:
            self.widgets[_widget].configure(state=NORMAL)
        lpower = self.last_status.get(tc.LEFTPOWER, 0)
        rpower = self.last_status.get(tc.RIGHTPOWER, 0)
        self.leftPeltierPowerString.set(str(lpower))
        self.rightPeltierPowerString.set(str(rpower))
        _state = self.last_status.get(tc.PELTIERON, [False, False])
        if _state[0] is True:
            self.left_peltier_on.set(1)
        else:
            self.left_peltier_on.set(0)
        if _state[1] is True:
            self.right_peltier_on.set(1)
        else:
            self.right_peltier_on.set(0)
        self._getTemp()
        self._getflow()
        self._readTemps()

    def _getTemp(self, *args, **kwargs):
        try:
            if float(self.lefttargettemp.get()) != self.last_status.get(tc.LEFTTARGET, 25.0):
                self.lefttargettemp.set(self.last_status.get(tc.LEFTTARGET, 25.0))
        except ValueError:
            pass
        try:
            if float(self.righttargettemp.get()) != self.last_status.get(tc.RIGHTTARGET, 25.0):
                self.righttargettemp.set(self.last_status.get(tc.RIGHTTARGET, 25.0))
        except ValueError:
            pass

    def _setTemp(self, *args):
        if not self.initialized:
            return
        try:
            float(self.lefttargettemp.get())
            print(f"Setting peltier to left:{self.lefttargettemp.get()} °C")
            self.sendcommand(tc.SETLEFTTEMP, self.lefttargettemp.get())
        except ValueError:
            pass
        try:
            float(self.righttargettemp.get())
            print(f"right:{self.righttargettemp.get()} °C")
            self.sendcommand(tc.SETRIGHTTEMP, self.righttargettemp.get())
        except ValueError:
            pass

    def _readTemps(self, **kwargs):
        self._lt = float(self.last_status.get(LEFT, -999.9))
        self._rt = float(self.last_status.get(RIGHT, -999.9))
        if self._lt > -1000:
            self.leftTempString.set('left: %0.2f °C' % self._lt)
        if self._rt > -1000:
            self.rightTempString.set('right: %0.2f °C' % self._rt)

    def _heatcoolbuttonclick(self, widget):
        _state = self.widgets[widget]['text']
        _sides = {'L':tc.LEFT, 'R':tc.RIGHT}
        if _state == 'Heat':
            self.widgets[widget].config(text='Cool')
            self.sendcommand(_sides[widget.upper()[0]]+tc.COOL)
        elif _state == 'Cool':
            self.widgets[widget].config(text='Heat')
            self.sendcommand(_sides[widget.upper()[0]]+tc.HEAT)

    def _getflow(self, *args, **kwargs):
        # _msg = kwargs.get('msg', self.readserial())
        self.widgets['leftheatcoolButton'].config(text=self.last_status.get(tc.LEFTFLOW, "?").capitalize())
        self.widgets['rightheatcoolButton'].config(text=self.last_status.get(tc.RIGHTFLOW, "?").capitalize())

    @property
    def temps(self):
        self._readTemps()
        return {'left': self._lt, 'right': self._rt}

class SeebeckMeas(Meas):

    _port = tc.THERMO_PORT
    _v = 0.0

    def createWidgets(self):
        self.left_temp_reading = StringVar(value='0.0')
        self.right_temp_reading = StringVar(value='0.0')
        self.voltage_reading = StringVar(value='0.0')
        tempFrame = tk.LabelFrame(self,
                                  text='Surface Temperatures (°C)',
                                  labelanchor=N)
        tk.Label(tempFrame,
                 padding=5,
                 text='Left: ').pack(side=LEFT)
        tk.Label(tempFrame,
                 padding=5,
                 textvariable=self.left_temp_reading).pack(side=LEFT)
        tk.Label(tempFrame,
                 padding=5,
                 textvariable=self.left_temp_reading).pack(side=RIGHT)
        tk.Label(tempFrame,
                 padding=5,
                 text='Right: ').pack(side=RIGHT)
        voltFrame = tk.LabelFrame(self,
                                  text='Surface Voltage (V)',
                                  labelanchor=N)
        tk.Label(voltFrame,
                 textvariable=self.voltage_reading).pack(side=TOP)
        deviceFrame = tk.LabelFrame(self,
                                    text='Device Settings',
                                    labelanchor=N)
        tk.Label(deviceFrame,
                 text='Address:').pack(side=LEFT)
        tk.Entry(deviceFrame,
                 width=15,
                 textvariable=self.addr).pack(side=LEFT)
        tempFrame.pack(side=TOP)
        voltFrame.pack(side=TOP)
        deviceFrame.pack(side=TOP)

    def readtemps(self, *args):
        self._lt = self.last_status.get('left', -999.99)
        self._rt = self.last_status.get.get('right', -999.99)
        self._v = self.last_status.get.get('voltage', 0.0)
        self.left_temp_reading.set(f'{self._lt:0.2f}')
        self.right_temp_reading.set(f'{self._rt:0.2f}')
        self.voltage_reading.set(f'{self._v:0.4f}')

    @property
    def voltage(self):
        return self._v

    @property
    def temps(self):
        self.readtemps()
        return {'left': self._lt, 'right': self._rt}

def ping(host):
    if host is not None:
        _ping = subprocess.run(['which','ping'], capture_output=True)
        p = subprocess.run([_ping.stdout.decode('utf-8').strip(), '-q', '-c1', '-W1', '-n', host], stdout=subprocess.PIPE)
        if p.returncode == 0:
            return True
    return False

def validateip(addr):
    try:
        a, b, c, d = addr.split(".")
        map(int, [a,b,c,d])
        return True
    except ValueError:
        pass
    return False

# def _checkconnetion(self, addr):
#     host, port = *addr
#     if not ping(host):
#         return False
#     try:
#         with Client((host, port), authkey=tc.AUTH_KEY) as client:
#             client.send(tc.COMMAND_STAT)
#             msg = client.recv()
#             if not isinstance(msg, dict):
#                 msg = {}
#         if msg.get('status', tc.STAT_ERROR) == tc.STAT_OK:
#             return True
#     except ConnectionRefusedError:
#         print(f"Host {addr.get().strip()} is down.")
#     return False

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
