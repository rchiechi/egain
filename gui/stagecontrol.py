import os
import time
import platform
import logging
import threading
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, DoubleVar, Listbox, Label, Entry
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, NONE, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
from stage.backend import NetHost, GenericBackEnd
from stage.mks import ESP302

class StageControls(tk.Frame):

    Xaxis = 1
    Yaxis = 2
    Zaxis = 3
    relative_move = 1.0
    unit = 1
    units = {1:'step',
             2:'mm',
             3:'μm'}

    def __init__(self, root, **kwargs):
        self.master = root
        self.busy = kwargs['busy']
        super().__init__(self.master)
        self.relative_move_label = StringVar()
        self.unitStr = StringVar()
        self.createWidgets()
        self.alive = threading.Event()
        self.alive.set()
        nethost = GenericBackEnd()
        self.stage = ESP302(self.alive, nethost)
        self.stage.start()

    def shutdown(self):
        self.alive.clear()

    def createWidgets(self):
        xyzFrame = tk.Frame(self)
        # commandFrame = tk.Frame(self)

        self.upButton = tk.Button(master=xyzFrame,
                                  text="Up",
                                  command=self.upButtonClick)
        self.downButton = tk.Button(master=xyzFrame,
                                    text="Down",
                                    command=self.downButtonClick)
        self.leftButton = tk.Button(master=xyzFrame,
                                    text="Left",
                                    command=self.leftButtonClick)
        self.rightButton = tk.Button(master=xyzFrame,
                                     text="Right",
                                     command=self.rightButtonClick)
        self.forwardButton = tk.Button(master=xyzFrame, text="Forward",
                                       command=self.forwardButtonClick)
        self.backButton = tk.Button(master=xyzFrame,
                                    text="Back",
                                    command=self.backButtonClick)

        relativemoveFrame = tk.Frame(xyzFrame)
        self.relativemoveScale = tk.Scale(master=relativemoveFrame,
                                          from_=1, to=1000,
                                          value=1,
                                          orient=HORIZONTAL,
                                          command=self.relativemoveScaleChange)
        relativemoveLabel = tk.Label(master=relativemoveFrame,
                                     text='Relative Move Distance')
        relativemoveindicatorLabel = tk.Label(master=relativemoveFrame,
                                              textvariable=self.relative_move_label)
        self.unitStr.set(self.units[1])
        unitOptionMenu = tk.OptionMenu(relativemoveFrame,
                                       self.unitStr,
                                       self.unitStr.get(),
                                       *list(self.units.values()))
        self.unitStr.trace_add('write', self._handleunitchange)
        self.relativemoveScaleChange(self.relativemoveScale.get())
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

        xyzFrame.pack(side=TOP)
        # commandFrame.pack(side=BOTTOM)
        print("Yo")

    def _waitformotion(self, widget):
        if self.stage.isMoving:
            self.busy.set(True)
            widget.after('100', lambda: self._waitformotion(widget))
        else:
            widget['state'] = NORMAL
            self.busy.set(False)

    def upButtonClick(self):
        self.upButton['state'] = DISABLED
        self.upButton.after('100', lambda: self._waitformotion(self.upButton))
        # self.stage.moveMax(self.Zaxis)
        self.stage.relativeMove(self.Zaxis, self.relative_move)

    def downButtonClick(self):
        self.downButton['state'] = DISABLED
        self.downButton.after('100', lambda: self._waitformotion(self.downButton))
        # self.stage.moveMin(self.Zaxis)
        self.stage.relativeMove(self.Zaxis, -1.0*self.relative_move)

    def rightButtonClick(self):
        self.rightButton['state'] = DISABLED
        self.rightButton.after('100', lambda: self._waitformotion(self.rightButton))
        # self.stage.moveMin(self.Yaxis)
        self.stage.relativeMove(self.Yaxis, self.relative_move)

    def leftButtonClick(self):
        self.leftButton['state'] = DISABLED
        self.leftButton.after('100', lambda: self._waitformotion(self.leftButton))
        # self.stage.moveMax(self.Yaxis)
        self.stage.relativeMove(self.Yaxis, -1.0*self.relative_move)

    def forwardButtonClick(self):
        self.forwardButton['state'] = DISABLED
        self.forwardButton.after('100', lambda: self._waitformotion(self.forwardButton))
        # self.stage.moveMax(self.Xaxis)
        self.stage.relativeMove(self.Xaxis, self.relative_move)

    def backButtonClick(self):
        self.backButton['state'] = DISABLED
        self.backButton.after('100', lambda: self._waitformotion(self.backButton))
        # self.stage.moveMin(self.Xaxis)
        self.stage.relativeMove(self.Xaxis, -1.0*self.relative_move)

    def _handleunitchange(self, *args):
        for key in self.units:
            if self.units[key] == self.unitStr.get():
                self.unit = key
                self.relativemoveScaleChange(self.relativemoveScale.get())
                self.stage.setUnits(key)
                time.sleep(1)
                for _unit in self.stage.getUnits():
                    if _unit != self.unit:
                        print("Warning units not set correctly.")

    def relativemoveScaleChange(self, distance):
        distance = float(distance)
        if self.unit in (1,3):
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
