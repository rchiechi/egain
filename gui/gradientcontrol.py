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

TEMPS = {'LEFT':None, 'RIGHT':None}
DEFAULTUSBDEVICE = 'Choose USB Device'

class TempControl(tk.Frame):

    controller = None
    is_initialized = False
    last_read = 0
    buffer = {}
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
        self.lefttargettemp.trace('w', self._setTemp)
        self.righttargettemp.trace('w', self._setTemp)
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
        self.widgets['rigthheatcoolButton'] = rigthheatcoolButton

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
        self.writeserial('OFFLEFT')
        self.writeserial('OFFRIGHT')

    def _setPeltier(self, side):
        if getattr(self, f'{side.lower()}_peltier_on').get():
            cmd = f'ON{side.upper()}'
        else:
            cmd = f'OFF{side.upper()}'
        if self.is_initialized:
            self.writeserial(cmd)

    def _checkPeltier(self, *args):
        if not self.is_initialized:
            return
        for _widget in self.widgets:
            self.widgets[_widget].configure(state=NORMAL)
        self.widgets['peltierRightCheck'].after('2000', self._checkPeltier)
        _msg = self.readserial()
        lpower = _msg.get('LeftPower', 0)
        rpower = _msg.get('RightPower', 0)
        self.leftPeltierPowerString.set(str(lpower))
        self.rightPeltierPowerString.set(str(rpower))
        _state = _msg.get('Peltier_on', [False, False])
        if _state[0] is True:
            self.left_peltier_on.set(1)
        else:
            self.left_peltier_on.set(0)
        if _state[1] is True:
            self.right_peltier_on.set(1)
        else:
            self.right_peltier_on.set(0)

    def _setTemp(self, *args):
        print(f"Setting peltier to left:{self.lefttargettemp.get()} right:{self.righttargettemp.get()} °C")
        self.writeserial('SETLTEMP', self.lefttargettemp.get())
        self.writeserial('SETRTEMP', self.righttargettemp.get())

    def _readTemps(self):
        self.tempFrame.after('500', self._readTemps)
        _temps = self.readserial()
        self.temps['left'] = float(_temps.get('LEFT', -999.9))
        self.temps['right'] = float(_temps.get('RIGHT', -999.9))
        if self.temps['left'] > -1000:
            self.leftTempString.set('left: %0.2f °C' % self.temps['left'])
        if self.temps['right'] > -1000:
            self.rightTempString.set('right: %0.2f °C' % self.temps['right'])

    def _heatcoolbuttonclick(self, widget):
        _state = self.widgets[widget]['text']
        if _state == 'Heat':
            self.widgets[widget].config(text='Cool')
            self.writeserial(f'{widget.upper()[0]}COOL')
        elif _state == 'Cool':
            self.widgets[widget].config(text='Heat')
            self.writeserial(f'{widget.upper()[0]}HEAT')

    def _initdevice(self, *args):
        if self.device.get() == DEFAULTUSBDEVICE or self.is_initialized is True:
            return
        print("Initializing device...", end='')
        n = 0
        ser_port = os.path.join('/', 'dev', self.device.get())
        if not os.path.exists(ser_port):
            return
        try:
            self.controller = serial.Serial(ser_port, 9600, timeout=1)
            _json = ''
            while not _json or n < 10:
                time.sleep(1)
                _json = str(self.controller.readline(), encoding='utf8')
                try:
                    _msg = json.loads(_json)
                    _val = _msg.get('message', '')
                    if _val == 'Done initializing thermocouples':
                        print("\nDevice initalized")
                        self.is_initialized = True
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
            return self.buffer
        try:
            _json = ''
            while not _json:
                self.writeserial('POLL')
                _json = str(self.controller.readline(), encoding='utf8').strip()
                try:
                    msg = json.loads(_json)
                    self.last_read = time.time()
                    self.buffer = msg
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
        return self.buffer

    def writeserial(self, cmd, val=None):
        if not self.is_initialized:
            return
        if not cmd:
            return
        try:
            self.controller.write(bytes(cmd, encoding='utf8')+b';')
            # print(f"Wrote {cmd};", end="")
            if val is not None:
                self.controller.write(bytes(val, encoding='utf8'))
                print(f"{val}", end="")
            # print(f" to {self.controller.name}.")
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
