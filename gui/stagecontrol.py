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
    relative_move = 1.0
    unit = 2
    units = {0:'counts',
             1:'steps',
             2:'mm',
             3:'μm'}
    xyzstage = {'address':IP_ADDRESS,
                'port':PORT,
                'nethost': None,
                'stage': None,
                'initialized': False}
    widgets = {}

    def __init__(self, root, **kwargs):
        self.master = root
        self.busy = kwargs['busy']
        super().__init__(self.master)
        self.relative_move_label = StringVar()
        self.unitStr = StringVar()
        self.createWidgets()
        self.alive = threading.Event()
        self.alive.set()
        # self.smuaddressvar = StringVar(value=IP_ADDRESS)
        # self.smuportvar = StringVar(value=PORT)
        # nethost = GenericBackEnd()
        # self.xyzstage['stage'] = ESP302(self.alive, nethost)
        # self.xyzstage['stage'].start()

    @property
    def initialized(self):
        return self.xyzstage['initialized']

    def shutdown(self):
        self.alive.clear()

    def createWidgets(self):
        xyzFrame = tk.Frame(self)
        # commandFrame = tk.Frame(self)

        self.upButton = tk.Button(master=xyzFrame,
                                  text="Up",
                                  command=self.upButtonClick,
                                  state=DISABLED)
        self.downButton = tk.Button(master=xyzFrame,
                                    text="Down",
                                    command=self.downButtonClick,
                                    state=DISABLED)
        self.leftButton = tk.Button(master=xyzFrame,
                                    text="Left",
                                    command=self.leftButtonClick,
                                    state=DISABLED)
        self.rightButton = tk.Button(master=xyzFrame,
                                     text="Right",
                                     command=self.rightButtonClick,
                                     state=DISABLED)
        self.forwardButton = tk.Button(master=xyzFrame, text="Forward",
                                       command=self.forwardButtonClick,
                                       state=DISABLED)
        self.backButton = tk.Button(master=xyzFrame,
                                    text="Back",
                                    command=self.backButtonClick,
                                    state=DISABLED)

        relativemoveFrame = tk.Frame(xyzFrame)
        self.relativemoveScale = tk.Scale(master=relativemoveFrame,
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
        stageaddressvar = StringVar(value=IP_ADDRESS)
        stageportvar = StringVar(value=PORT)
        stageaddressLabel = tk.Label(master=stageFrame, text='Address:')
        stageaddressEntry = tk.Entry(master=stageFrame,
                                     textvariable=stageaddressvar,
                                     width=12)
        stageportlLabel = tk.Label(master=stageFrame, text='Port:')
        stageportEntry = tk.Entry(master=stageFrame,
                                  textvariable=stageportvar,
                                  width=4)
        self.xyzstage['address'] = stageaddressvar
        self.xyzstage['port'] = stageportvar
        initButton = tk.Button(master=stageFrame,
                               text='Initialize',
                               command=self.initButtonClick)
        self.widgets['initButton'] = initButton
        self.widgets['stageaddressEntry'] = stageaddressEntry
        self.widgets['stageportEntry'] = stageportEntry

        relativemoveLabel.pack(side=TOP)
        self.relativemoveScale.pack(side=TOP)
        relativemoveindicatorLabel.pack(side=TOP)
        relativemoveFrame.pack(side=RIGHT, fill=NONE)
        unitOptionMenu.pack(side=BOTTOM)
        self.upButton.pack(side=TOP)
        self.downButton.pack(side=BOTTOM)
        self.leftButton.pack(side=LEFT)
        self.rightButton.pack(side=RIGHT)
        self.backButton.pack(side=BOTTOM)
        self.forwardButton.pack(side=BOTTOM)

        stageaddressLabel.pack(side=LEFT)
        stageaddressEntry.pack(side=LEFT)
        stageportlLabel.pack(side=LEFT)
        stageportEntry.pack(side=LEFT)
        initButton.pack(side=BOTTOM)
        stageFrame.pack(side=BOTTOM)

        xyzFrame.pack(side=TOP)
        # commandFrame.pack(side=BOTTOM)

    def _waitformotion(self, widget):
        if self.xyzstage['stage'].isMoving:
            self.busy.set(True)
            widget.after('100', lambda: self._waitformotion(widget))
        else:
            widget['state'] = NORMAL
            self.busy.set(False)

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
            self.relativemoveScaleChange(self.relativemoveScale.get())
            for _widget in 'relativemoveScale', 'upButton', 'downButton', \
                           'leftButton', 'rightButton', 'forwardButton', 'backButton':
                getattr(self, _widget)['state'] = NORMAL
            self._handleunitchange()

        except IOError:
            self.xyzstage['initialized'] = False

    def upButtonClick(self):
        self.upButton['state'] = DISABLED
        self.upButton.after('100', lambda: self._waitformotion(self.upButton))
        # self.xyzstage['stage'].moveMax(self.Zaxis)
        self.xyzstage['stage'].relativeMove(self.Zaxis, self.relative_move)

    def downButtonClick(self):
        self.downButton['state'] = DISABLED
        self.downButton.after('100', lambda: self._waitformotion(self.downButton))
        # self.xyzstage['stage'].moveMin(self.Zaxis)
        self.xyzstage['stage'].relativeMove(self.Zaxis, -1.0*self.relative_move)

    def rightButtonClick(self):
        self.rightButton['state'] = DISABLED
        self.rightButton.after('100', lambda: self._waitformotion(self.rightButton))
        # self.xyzstage['stage'].moveMin(self.Yaxis)
        self.xyzstage['stage'].relativeMove(self.Yaxis, self.relative_move)

    def leftButtonClick(self):
        self.leftButton['state'] = DISABLED
        self.leftButton.after('100', lambda: self._waitformotion(self.leftButton))
        # self.xyzstage['stage'].moveMax(self.Yaxis)
        self.xyzstage['stage'].relativeMove(self.Yaxis, -1.0*self.relative_move)

    def forwardButtonClick(self):
        self.forwardButton['state'] = DISABLED
        self.forwardButton.after('100', lambda: self._waitformotion(self.forwardButton))
        # self.xyzstage['stage'].moveMax(self.Xaxis)
        self.xyzstage['stage'].relativeMove(self.Xaxis, self.relative_move)

    def backButtonClick(self):
        self.backButton['state'] = DISABLED
        self.backButton.after('100', lambda: self._waitformotion(self.backButton))
        # self.xyzstage['stage'].moveMin(self.Xaxis)
        self.xyzstage['stage'].relativeMove(self.Xaxis, -1.0*self.relative_move)

    def _handleunitchange(self, *args):
        for key in self.units:
            if self.units[key] == self.unitStr.get():
                self.unit = key
                print(f"Setting units to {self.units[key]}")
                self.relativemoveScaleChange(self.relativemoveScale.get())
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
                self.relativemoveScale.set(distance)
            _distance = f'{distance:.2f}'
        self.relativemoveScale['to'] = _range

        _labelstring = f'{_distance} {self.units[self.unit]}'
        if abs(distance) > 1 and self.unit == 1:
            _labelstring += 's'
        self.relative_move_label.set(_labelstring)
        self.relative_move = distance
