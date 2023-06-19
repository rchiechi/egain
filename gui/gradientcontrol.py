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
from pi.shared import THERMO_PORT, VOLTA_PORT, COMMKEY, COMMAND_READ, COMMAND_STAT, STAT_OK, STAT_ERROR

TEMPS = {'LEFT':None, 'RIGHT':None}
DEFAULTUSBDEVICE = 'Choose USB Device'

class TempControl(tk.Frame):

    controller = None
    is_initialized = False
    last_read = 0
    last_write = 0
    readbuffer = {}
    temps = {'left':0, 'right':0}
    widgets = {}

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.leftTempString = StringVar()
        self.rightTempString = StringVar()
        self.leftPeltierPowerString = StringVar()
        self.rightPeltierPowerString = StringVar()
        self.device = StringVar()
        self.lefttargettemp = StringVar()
        self.righttargettemp = StringVar()
        self.left_peltier_on = IntVar()
        self.right_peltier_on = IntVar()
        self.createWidgets()

    @property
    def initialized(self):
        return self.is_initialized

    @property
    def lefttemp(self):
        return self.temps['left']

    @property
    def righttemp(self):
        return self.temps['right']

    @property
    def peltierstatus(self):
        return {'left': bool(self.left_peltier_on.get()),
                'right': bool(self.right_peltier_on.get())}

    def createWidgets(self):
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
        setLeftTemp = tk.Entry(setFrame, textvariable=self.lefttargettemp, width=4)
        setRightTemp = tk.Entry(setFrame, textvariable=self.righttargettemp, width=4)
        self.lefttargettemp.set("25.0")
        self.righttargettemp.set("25.0")
        for n in ('<Return>', '<Leave>', '<Enter>'):
            setLeftTemp.bind(n, self._setTemp)
            setRightTemp.bind(n, self._setTemp)
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

        devicePicker = tk.OptionMenu(self,
                                     self.device,
                                     DEFAULTUSBDEVICE,
                                     *_enumerateDevices())
        self.device.trace_add('write', self._initdevice)

        setLeftTemp.pack(side=LEFT)
        leftPeltierPower.pack(side=LEFT)
        setRightTemp.pack(side=LEFT)
        rightPeltierPower.pack(side=LEFT)
        peltierRightCheck.pack(side=RIGHT)
        peltierLeftCheck.pack(side=RIGHT)
        devicePicker.pack()
        leftTemp.pack(side=TOP, expand=False)
        rightTemp.pack(side=BOTTOM)
        leftheatcoolButton.pack(side=LEFT)
        rigthheatcoolButton.pack(side=LEFT)
        toggleFrame.pack(side=TOP)
        heatcoolFrame.pack(side=TOP)
        setFrame.pack(side=TOP)
        self.tempFrame.pack(side=TOP)

        for _widget in self.widgets:
            self.widgets[_widget].configure(state=DISABLED)

        self._readTemps()

    def shutdown(self):
        self.writeserial('LEFTOFF')
        self.writeserial('RIGHTOFF')

    def _setPeltier(self, side):
        if getattr(self, f'{side.lower()}_peltier_on').get():
            cmd = f'{side.upper()}ON'
        else:
            cmd = f'{side.upper()}OFF'
        if self.is_initialized:
            self.writeserial(cmd)

    def _checkPeltier(self, *args):
        if not self.is_initialized:
            return
        for _widget in self.widgets:
            self.widgets[_widget].configure(state=NORMAL)
        self.widgets['peltierRightCheck'].after('1000', self._checkPeltier)
        _msg = self.readserial()
        lpower = _msg.get('LEFTPOWER', 0)
        rpower = _msg.get('RIGHTPOWER', 0)
        self.leftPeltierPowerString.set(str(lpower))
        self.rightPeltierPowerString.set(str(rpower))
        _state = _msg.get('PELTIERON', [False, False])
        if _state[0] is True:
            self.left_peltier_on.set(1)
        else:
            self.left_peltier_on.set(0)
        if _state[1] is True:
            self.right_peltier_on.set(1)
        else:
            self.right_peltier_on.set(0)
        self._getTemp(msg=_msg)
        self._getflow(msg=_msg)
        self._readTemps(msg=_msg)

    def _getTemp(self, *args, **kwargs):
        if not self.is_initialized:
            return
        _msg = kwargs.get('msg', self.readserial())
        try:
            if float(self.lefttargettemp.get()) != _msg.get('LEFTTARGET', 25.0):
                self.lefttargettemp.set(_msg.get('LEFTTARGET', 25.0))
        except ValueError:
            pass
        try:
            if float(self.righttargettemp.get()) != _msg.get('RIGHTTARGET', 25.0):
                self.righttargettemp.set(_msg.get('RIGHTTARGET', 25.0))
        except ValueError:
            pass

    def _setTemp(self, *args):
        if not self.is_initialized:
            return
        try:
            float(self.lefttargettemp.get())
            print(f"Setting peltier to left:{self.lefttargettemp.get()} °C")
            self.writeserial('SETLEFTTEMP', self.lefttargettemp.get())
        except ValueError:
            pass
        try:
            float(self.righttargettemp.get())
            print(f"right:{self.righttargettemp.get()} °C")
            self.writeserial('SETRIGHTTEMP', self.righttargettemp.get())
        except ValueError:
            pass

    def _readTemps(self, **kwargs):
        # self.tempFrame.after('500', self._readTemps)
        _temps = kwargs.get('msg', self.readserial())
        self.temps['left'] = float(_temps.get('LEFT', -999.9))
        self.temps['right'] = float(_temps.get('RIGHT', -999.9))
        if self.temps['left'] > -1000:
            self.leftTempString.set('left: %0.2f °C' % self.temps['left'])
        if self.temps['right'] > -1000:
            self.rightTempString.set('right: %0.2f °C' % self.temps['right'])

    def _heatcoolbuttonclick(self, widget):
        _state = self.widgets[widget]['text']
        _sides = {'L':'LEFT', 'R':'RIGHT'}
        if _state == 'Heat':
            self.widgets[widget].config(text='Cool')
            self.writeserial(f'{_sides[widget.upper()[0]]}COOL')
        elif _state == 'Cool':
            self.widgets[widget].config(text='Heat')
            self.writeserial(f'{_sides[widget.upper()[0]]}HEAT')

    def _getflow(self, *args, **kwargs):
        _msg = kwargs.get('msg', self.readserial())
        self.widgets['leftheatcoolButton'].config(text=_msg.get("LEFTFLOW", "?").capitalize())
        self.widgets['rightheatcoolButton'].config(text=_msg.get("RIGHTFLOW", "?").capitalize())

    def _initdevice(self, *args):
        if self.device.get() == DEFAULTUSBDEVICE or self.is_initialized is True:
            return
        print("Initializing device...", end='')
        n = 0
        ser_port = os.path.join('/', 'dev', self.device.get())
        if not os.path.exists(ser_port):
            return
        try:
            self.controller = serial.Serial(ser_port, 115200, timeout=1)
            _json = ''
            while not _json or n < 10:
                time.sleep(1)
                _json = str(self.controller.readline(), encoding='utf8')
                try:
                    _msg = json.loads(_json)
                    _val = _msg.get('message', '')
                    if _val == 'INITIALIZED':
                        print("\nDevice initalized")
                        self.is_initialized = True
                        time.sleep(0.5)
                        self.writeserial('SHOWSTATUS')
                        time.sleep(0.5)
                        self._checkPeltier()
                        return
                except json.decoder.JSONDecodeError:
                    print(f"{n}...", end='')
                n += 1
        except serial.serialutil.SerialException:
            return
        print("\nEmpty reply from device.")

    def readserial(self):
        if not self.is_initialized:
            return {}
        if time.time() - self.last_read < 0.5:
            return self.readbuffer
        try:
            _json = ''
            while not _json:
                self.writeserial('POLL')
                _json = str(self.controller.readline(), encoding='utf8').strip()
                try:
                    msg = json.loads(_json)
                    self.last_read = time.time()
                    self.readbuffer = msg
                    # print(msg)
                    if 'message' in msg:
                        print(msg)
                        self.is_initialized = False
                    return msg
                except json.decoder.JSONDecodeError as err:
                    print(f'JSON Error: {err}')
        except serial.serialutil.SerialException:
            pass
        print(f"Error reading from {self.controller.name}.")
        return self.readbuffer

    def writeserial(self, cmd, val=None):
        if not self.is_initialized:
            return
        if not cmd:
            return
        if time.time() - self.last_write < 0.5:
            time.sleep(0.5)
        try:
            self.controller.write(bytes(cmd, encoding='utf8')+b';')
            # print(f"Wrote {cmd};", end="")
            if val is not None:
                self.controller.write(bytes(val, encoding='utf8'))
                # print(f"{val}", end="")
            # print(f" to {self.controller.name}.")
        except serial.serialutil.SerialException:
            print(f"Error sending command to {self.controller.name}.")
        self.last_write = time.time()


class SeebeckMeas(tk.Frame):

    _lt = 0.0
    _rt = 0.0
    _v = 0.0
    _initialized = False
    widgets = {}

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.left_temp_reading = StringVar(value='0.0')
        self.right_temp_reading = StringVar(value='0.0')
        self.voltage_reading = StringVar(value='0.0')
        self.addr = StringVar(value=f'127.0.0.1:{THERMO_PORT}')
        self.createWidgets()
        self.readtemps()

    def createWidgets(self):
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

    def _checkconnetion(self):
        if not ping(self.host):
            self._initalized = False
            return False
        try:
            with Client((self.host, self.port), authkey=COMMKEY) as client:
                client.send(COMMAND_STAT)
                msg = client.recv()
                if not isinstance(msg, dict):
                    msg = {}
            if msg.get('status', STAT_ERROR) == STAT_OK:
                self._initalized = True
                return True
        except ConnectionRefusedError:
            print(f"Host {self.addr.get().strip()} is down.")
        self._initalized = False
        return False

    def readtemps(self, *args):
        if not self.connected:
            self.after(5000, self.readtemps)
            return
        with Client((self.host, self.port), authkey=COMMKEY) as client:
            client.send(COMMAND_READ)
            msg = client.recv()
            if not isinstance(msg, dict):
                msg = {}
        self._lt = msg.get('left', -999.99)
        self._rt = msg.get('right', -999.99)
        self._v = msg.get('voltage', 0.0)
        self.left_temp_reading.set(f'{self._lt:0.2f}')
        self.right_temp_reading.set(f'{self._rt:0.2f}')
        self.voltage_reading.set(f'{self._v:0.4f}')
        self.after(1000, self.readtemps)

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
        return self._initalized
    @property
    def temps(self):
        self.readtemps()
        return {'left': self._lt, 'right': self._rt}


def ping(host):
    if host is not None:
        p = subprocess.run(['/usr/bin/ping', '-q', '-c1', '-W1', '-n', host], stdout=subprocess.PIPE)
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
