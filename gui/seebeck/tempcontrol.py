import tkinter.ttk as tk
from tkinter import IntVar, StringVar
from tkinter import N
from tkinter import TOP, BOTTOM, LEFT, RIGHT
from tkinter import DISABLED, NORMAL

import thermo.constants as tc
from gui.seebeck.meas import Meas

class TempControl(Meas):

    _port = tc.PELTIER_PORT
    last_temps = {'left':25.0, 'right':25.0}
    config_file = 'TempControl.json'
    ok_to_update = True

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
        setlefttempEntry = tk.Entry(setFrame, textvariable=self.lefttargettemp, width=4)
        setrighttempEntry = tk.Entry(setFrame, textvariable=self.righttargettemp, width=4)
        self.lefttargettemp.set("25.0")
        self.righttargettemp.set("25.0")
        for n in ('<Return>', '<Tab>'):
            setlefttempEntry.bind(n, self._setTemp)
            setrighttempEntry.bind(n, self._setTemp)

        toggleFrame = tk.Frame(self)
        peltierLeftCheck = tk.Checkbutton(toggleFrame,
                                          text='Left Peliter On',
                                          variable=self.left_peltier_on,
                                          command=lambda: self._setPeltier('LEFT'))
        peltierRightCheck = tk.Checkbutton(toggleFrame,
                                           text='Right Peliter On',
                                           variable=self.right_peltier_on,
                                           command=lambda: self._setPeltier('RIGHT'))
        for _widget in (setlefttempEntry, setrighttempEntry, peltierLeftCheck, peltierRightCheck):
            _widget.bind("<Enter>", self._set_not_ok_to_update)
            _widget.bind("<Leave>", self._set_ok_to_update)

        self.widgets['peltierLeftCheck'] = peltierLeftCheck
        self.widgets['peltierRightCheck'] = peltierRightCheck
        heatcoolFrame = tk.Frame(self)
        leftheatcoolButton = tk.Button(heatcoolFrame, text="Heat",
                                       command=lambda: self._heatcoolbuttonclick('leftheatcoolButton'),
                                       width=5)
        rigthheatcoolButton = tk.Button(heatcoolFrame, text="Cool",
                                        command=lambda: self._heatcoolbuttonclick('rightheatcoolButton'),
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

        setlefttempEntry.pack(side=LEFT)
        leftPeltierPower.pack(side=LEFT)
        setrighttempEntry.pack(side=LEFT)
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
            cmd = getattr(tc, f'{side.upper()}ON')
        else:
            cmd = getattr(tc, f'{side.upper()}OFF')
        if self.initialized:
            self.sendcommand(cmd)

    def _set_not_ok_to_update(self, *args):
        self.ok_to_update = False

    def _set_ok_to_update(self, *args):
        self.ok_to_update = True

    def _checkPeltier(self, *args):
        self.after('1000', self._checkPeltier)
        if not self.initialized:
            return
        for _widget in self.widgets:
            self.widgets[_widget].configure(state=NORMAL)
        lpower = self.last_status.get(tc.LEFTPOWER, 0)
        rpower = self.last_status.get(tc.RIGHTPOWER, 0)
        self.leftPeltierPowerString.set(str(lpower))
        self.rightPeltierPowerString.set(str(rpower))
        if not self.ok_to_update:
            return
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
            if self.last_temps['left'] != self.last_status.get(tc.LEFTTARGET, 25.0):
                self.lefttargettemp.set(self.last_status.get(tc.LEFTTARGET, 25.0))
        except ValueError:
            pass
        try:
            if self.last_temps['right'] != self.last_status.get(tc.RIGHTTARGET, 25.0):
                self.righttargettemp.set(self.last_status.get(tc.RIGHTTARGET, 25.0))
        except ValueError:
            pass

    def _setTemp(self, *args):
        if not self.initialized:
            return
        self._set_not_ok_to_update()
        try:
            _temp = float(self.lefttargettemp.get())
            if _temp not in (self._lt, self.last_temps['left']):
                self.last_temps['left'] = _temp
                print(f"Setting left peltier: {_temp}°C")
                self.sendcommand(tc.SETLEFTTEMP, _temp)
        except ValueError:
            pass

        try:
            _temp = float(self.righttargettemp.get())
            if _temp not in (self._rt, self.last_temps['right']):
                self.last_temps['right'] = _temp
                print(f"Setting right peltier: {_temp}°C")
                self.sendcommand(tc.SETRIGHTTEMP, _temp)
        except ValueError:
            pass
        self._set_ok_to_update()

    def _readTemps(self, **kwargs):
        self._lt = float(self.last_status.get(tc.LEFT, -999.9))
        self._rt = float(self.last_status.get(tc.RIGHT, -999.9))
        if self._lt > -1000:
            self.leftTempString.set('left: %0.2f °C' % self._lt)
        if self._rt > -1000:
            self.rightTempString.set('right: %0.2f °C' % self._rt)

    def _heatcoolbuttonclick(self, widget):
        self._set_not_ok_to_update()
        _state = self.widgets[widget]['text']
        _sides = {'L':tc.LEFT, 'R':tc.RIGHT}
        if _state == 'Heat':
            self.widgets[widget].config(text='Cool')
            self.sendcommand(_sides[widget.upper()[0]]+tc.COOL)
        elif _state == 'Cool':
            self.widgets[widget].config(text='Heat')
            self.sendcommand(_sides[widget.upper()[0]]+tc.HEAT)
        self._set_ok_to_update()

    def _getflow(self, *args, **kwargs):
        self._set_not_ok_to_update()
        self.widgets['leftheatcoolButton'].config(text=self.last_status.get(tc.LEFTFLOW, "?").capitalize())
        self.widgets['rightheatcoolButton'].config(text=self.last_status.get(tc.RIGHTFLOW, "?").capitalize())
        self._set_ok_to_update()

    @property
    def temps(self):
        self._readTemps()
        return {'left': self._lt, 'right': self._rt}
