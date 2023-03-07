import os
import time
import platform
import logging
import threading
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, DoubleVar, Listbox, Label, Entry, messagebox
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, NONE, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
from stage.backend import NetHost, GenericBackEnd, IP_ADDRESS, PORT
from stage.mks import ESP302


class StageControls(tk.Frame):

    Xaxis = 2
    Yaxis = 1
    Zaxis = 3
    axismap = {'up': (Zaxis, 1.0),
               'down': (Zaxis, -1.0),
               'right': (Yaxis, 1.0),
               'left': (Yaxis, -1.0),
               'forward': (Xaxis, 1.0),
               'back': (Xaxis, -1.0)}
    relative_move = 1.0
    unit = 2
    units = {0: 'counts',
             1: 'steps',
             2: 'mm',
             3: 'μm'}
    xyzstage = {'address': IP_ADDRESS,
                'port': PORT,
                'nethost': None,
                'stage': None,
                'initialized': False}
    position = [0.0, 0.0, 0.0]
    widgets = {}
    motionControls = {}
    err_id = 0
    pos_id = 0

    def __init__(self, root, **kwargs):
        self.master = root
        self.busy = kwargs['busy']
        super().__init__(self.master)
        self.relative_move_label = StringVar()
        self.unitStr = StringVar()
        self.status = StringVar(value='Nominal')
        self.createWidgets()
        self.alive = threading.Event()
        self.alive.set()

    @property
    def initialized(self):
        return self.xyzstage['initialized']

    def shutdown(self):
        self.alive.clear()

    def createWidgets(self):
        xyzFrame = tk.Frame(self)
        # commandFrame = tk.Frame(self)
        for _button in self.axismap:
            self.motionControls[_button] = tk.Button(master=xyzFrame,
                                                     text=_button.capitalize(),
                                                     command=lambda: self.motionButtonClick(_button),
                                                     state=DISABLED)

        relativemoveFrame = tk.Frame(xyzFrame)
        self.motionControls['scale'] = tk.Scale(master=relativemoveFrame,
                                                from_=1, to=1000,
                                                value=1,
                                                orient=HORIZONTAL,
                                                command=self.relativemoveScaleChange,
                                                state=DISABLED)
        relativemoveLabel = tk.Label(master=relativemoveFrame,
                                     text='Relative Move Distance')
        relativemoveindicatorLabel = tk.Label(master=relativemoveFrame,
                                              textvariable=self.relative_move_label)
        self.unitStr.set(self.units[2])
        unitOptionMenu = tk.OptionMenu(relativemoveFrame,
                                       self.unitStr,
                                       self.unitStr.get(),
                                       *list(self.units.values()))
        # self.unitStr.trace_add('write', self._handleunitchange)
        # self.relativemoveScaleChange(self.relativemoveScale.get())

        stageFrame = tk.Frame(master=self)
        positionFrame = tk.Frame(master=stageFrame)
        gohomebutton = tk.Button(master=positionFrame,
                                 text='Go Home',
                                 command=self.gohomeButtonClick,
                                 state=DISABLED)
        self.widgets['gohomebutton'] = gohomebutton
        stagepositionLabel = tk.Label(master=positionFrame, text='Position:')
        self.widgets['stagepositionvar'] = StringVar(value=str(self.position))
        # self.widgets['stagepositionvar'].trace_add('w', self._updatepositionvar)
        stagepositionVal = tk.Label(master=positionFrame,
                                    textvariable=self.widgets['stagepositionvar'])
        statusLabel = tk.Label(master=stageFrame,
                               textvariable=self.status)
        addressFrame = tk.Frame(master=stageFrame)

        stageaddressvar = StringVar(value=IP_ADDRESS)
        stageportvar = StringVar(value=PORT)
        stageaddressLabel = tk.Label(master=addressFrame, text='Address:')
        stageaddressEntry = tk.Entry(master=addressFrame,
                                     textvariable=stageaddressvar,
                                     width=12)
        stageportlLabel = tk.Label(master=addressFrame, text='Port:')
        stageportEntry = tk.Entry(master=addressFrame,
                                  textvariable=stageportvar,
                                  width=4)
        self.xyzstage['address'] = stageaddressvar
        self.xyzstage['port'] = stageportvar
        initButton = tk.Button(master=addressFrame,
                               text='Initialize',
                               command=self.initButtonClick)
        self.widgets['initButton'] = initButton
        self.widgets['stageaddressEntry'] = stageaddressEntry
        self.widgets['stageportEntry'] = stageportEntry

        relativemoveLabel.pack(side=TOP)
        self.motionControls['scale'].pack(side=TOP)
        relativemoveindicatorLabel.pack(side=TOP)
        relativemoveFrame.pack(side=RIGHT, fill=NONE)
        unitOptionMenu.pack(side=BOTTOM)
        self.motionControls['up'].pack(side=TOP)
        self.motionControls['down'].pack(side=BOTTOM)
        self.motionControls['left'].pack(side=LEFT)
        self.motionControls['right'].pack(side=RIGHT)
        self.motionControls['back'].pack(side=BOTTOM)
        self.motionControls['forward'].pack(side=BOTTOM)
        tk.Separator(positionFrame, orient=HORIZONTAL).pack(side=TOP, fill=X)

        gohomebutton.pack(side=LEFT)
        stagepositionLabel.pack(side=LEFT)
        stagepositionVal.pack(side=LEFT)
        statusLabel.pack(side=BOTTOM)
        positionFrame.pack(side=TOP)
        stageaddressLabel.pack(side=LEFT)
        stageaddressEntry.pack(side=LEFT)
        stageportlLabel.pack(side=LEFT)
        stageportEntry.pack(side=LEFT)
        addressFrame.pack(side=BOTTOM)
        initButton.pack(side=BOTTOM)
        stageFrame.pack(side=BOTTOM)

        xyzFrame.pack(side=TOP)
        # commandFrame.pack(side=BOTTOM)

    def _checkformotion(self):
        if self.xyzstage['stage'].isMoving:
            self.busy.set(True)
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = DISABLED
        self.widgets['gohomebutton']['state'] = DISABLED
        self.widgets['initButton'].after('100', lambda: self._waitformotion(self.widgets['initButton']))

    def _waitformotion(self, widget):
        if self.xyzstage['stage'].isMoving:
            self.busy.set(True)
            widget.after('100', lambda: self._waitformotion(widget))
        else:
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = NORMAL
            self.widgets['gohomebutton']['state'] = NORMAL
            self.busy.set(False)
        self._updateposition()
        
    def initButtonClick(self):
        _address, _port = self.xyzstage['address'].get(), self.xyzstage['port'].get()
        _ok = True
        for _i in _address.split('.'):
            try:
                int(_i)
            except ValueError:
                _ok = False
        try:
            int(_port)
        except ValueError:
            _ok = False
        if len(_address.split('.')) != 4:
            _ok = False
        if _ok:
            self._initstage()
        else:
            messagebox.showerror("Error", "Invalid address settings.")

    def _initstage(self):
        self.xyzstage['nethost'] = NetHost()
        self.xyzstage['nethost'].initialize(address=self.xyzstage['address'].get(),
                                            port=self.xyzstage['port'].get())
        self.xyzstage['stage'] = ESP302(self.alive, self.xyzstage['nethost'])
        try:
            self.xyzstage['stage'].start()
            self.xyzstage['initialized'] = True
            for _widget in 'initButton', 'stageaddressEntry', 'stageportEntry':
                self.widgets[_widget]['state'] = DISABLED
            self.unitStr.trace_add('write', self._handleunitchange)
            self.relativemoveScaleChange(self.motionControls['scale'].get())
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = NORMAL
            self.widgets['gohomebutton']['state'] = NORMAL
            self._handleunitchange()
            self.widgets['initButton'].after(100, self._updateposition)

        except IOError:
            self.xyzstage['initialized'] = False

    def _updateposition(self):
        if self.pos_id == 0:
            self.pos_id = self.position = self.xyzstage['stage'].getPosition()
        _res = self.xyzstage['stage'].getresult(self.pos_id)
        if _res is False:
            self.widgets['initButton'].after(100, self._updateposition)
            return
        self.position = _res
        self.widgets['stagepositionvar'].set(
            f'{self.position[0]:.2f},{self.position[1]:.2f},{self.position[2]:.2f}')
        # self.widgets['initButton'].after(500, self._updateposition)

    def checkErrors(self):
        if self.err_id == 0:
            self.err_id = self.xyzstage['stage'].getErrors()
        _res = self.xyzstage['stage'].getresult(self.err_id)
        if _res is False:
            self.widgets['initButton'].after(100, self.checkErrors)
            self.status.set('Nominal')
            return
        elif _res is not None:
            self.status.set(_res)
        self.err_id = 0

    def gohomeButtonClick(self):
        for _widget in self.motionControls:
            self.motionControls[_widget]['state'] = DISABLED
        self.widgets['gohomebutton']['state'] = DISABLED
        self.xyzstage['stage'].findHome()
        self.widgets['gohomebutton'].after('100', lambda: self._waitformotion(self.widgets['gohomebutton']))

    def motionButtonClick(self, _button):
        for _widget in self.motionControls:
            self.motionControls[_widget]['state'] = DISABLED
        self.widgets['gohomebutton']['state'] = DISABLED
        self.motionControls[_button].after('100', lambda: self._waitformotion(self.motionControls[_button]))
        self.xyzstage['stage'].relativeMove(self.axismap[_button][0], self.axismap[_button][1]*self.relative_move)
        self.checkErrors()
        time.sleep(0.5)

    def _handleunitchange(self, *args):
        for key in self.units:
            if self.units[key] == self.unitStr.get():
                self.unit = key
                print(f"Setting units to {self.units[key]}")
                self.relativemoveScaleChange(self.motionControls['scale'].get())
                self.xyzstage['stage'].setUnits(key)
                time.sleep(1)
                for _unit in self.xyzstage['stage'].getUnits():
                    if _unit != self.unit:
                        print("Warning units not set correctly.")

    def relativemoveScaleChange(self, distance):
        distance = float(distance)
        if self.unit in (1, 3):
            _distance = f'{distance:.0f}'
            _range = 1000
        else:
            _range = 20
            if distance > _range:
                distance = 0.0
                self.motionControls['scale'].set(distance)
            _distance = f'{distance:.2f}'
        self.motionControls['scale']['to'] = _range

        _labelstring = f'{_distance} {self.units[self.unit]}'
        if abs(distance) > 1 and self.unit == 1:
            _labelstring += 's'
        self.relative_move_label.set(_labelstring)
        self.relative_move = distance

    def checkErrors(self):
        if self.err_id == 0:
            self.err_id = self.xyzstage['stage'].getErrors()
        _res = self.xyzstage['stage'].getresult(self.err_id)
        if _res is False:
            self.widgets['initButton'].after(100, self.checkErrors)
            self.status.set('Nominal')
            return
        elif _res is not None:
            self.status.set(_res)
        self.err_id = 0
