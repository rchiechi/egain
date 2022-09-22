import os
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

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.relative_move_label = StringVar()
        self.createWidgets()
        self.alive = threading.Event()
        self.alive.set()
        # nethost = NetHost()
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
        relativemoveScale = tk.Scale(master=relativemoveFrame,
                                     from_=1, to=1000,
                                     orient=HORIZONTAL,
                                     command=self.relativemoveScaleChange)
        relativemoveLabel = tk.Label(master=relativemoveFrame,
                                     text='Relative Move Distance')
        relativemoveindicatorLabel = tk.Label(master=relativemoveFrame,
                                              textvariable=self.relative_move_label)
        self.relativemoveScaleChange(relativemoveScale.get())
        relativemoveLabel.pack(side=TOP)
        relativemoveScale.pack(side=TOP)
        relativemoveindicatorLabel.pack(side=TOP)
        relativemoveFrame.pack(side=RIGHT, fill=NONE)
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
            widget.after('100', lambda: self._waitformotion(widget))
        else:
            widget['state'] = NORMAL

    def upButtonClick(self):
        self.upButton['state'] = DISABLED
        self.upButton.after('100', lambda: self._waitformotion(self.upButton))
        self.stage.moveMax(self.Zaxis)

    def downButtonClick(self):
        self.downButton['state'] = DISABLED
        self.downButton.after('100', lambda: self._waitformotion(self.downButton))
        self.stage.moveMin(self.Zaxis)

    def leftButtonClick(self):
        self.leftButton['state'] = DISABLED
        self.leftButton.after('100', lambda: self._waitformotion(self.leftButton))
        self.stage.moveMax(self.Yaxis)

    def rightButtonClick(self):
        self.rightButton['state'] = DISABLED
        self.rightButton.after('100', lambda: self._waitformotion(self.rightButton))
        self.stage.moveMin(self.Yaxis)

    def forwardButtonClick(self):
        self.forwardButton['state'] = DISABLED
        self.forwardButton.after('100', lambda: self._waitformotion(self.forwardButton))
        self.stage.moveMax(self.Xaxis)
        return

    def backButtonClick(self):
        self.backButton['state'] = DISABLED
        self.backButton.after('100', lambda: self._waitformotion(self.backButton))
        self.stage.moveMin(self.Xaxis)

    def relativemoveScaleChange(self, distance):
        distance = float(distance)
        if self.unit in (1,3):
            _distance = f'{distance:.0f}'
        else:
            _distance = f'{distance:.2f}'
        self.relative_move_label.set(f'{_distance} {self.units[self.unit]}')
        self.relative_move = distance
