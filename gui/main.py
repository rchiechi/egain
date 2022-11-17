'''
Copyright (C) 2022 Ryan Chiechi <ryan.chiechi@ncsu.edu>
Description:

        This is the GUI front-end for the parsing engine. It mostly works ok,
        but some of the options configurable on the command line may not be
        implemented.

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os
import platform
import time
# import logging
# import threading
import tkinter.ttk as tk
# from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, BooleanVar, Listbox, Label, Entry
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
from gui.datacanvas import dataCanvas
from gui.stagecontrol import StageControls
from gui.tempcontrol import TempControl
from gui.measurement import MeasurementControl

absdir = os.path.dirname(os.path.realpath(__file__))

class MainFrame(tk.Frame):
    '''The main frame for collecting EGaIn data.'''

    widgets = {}
    variabels = {}

    def __init__(self, root, opts):
        self.root = root
        super().__init__(self.root)
        self.opts = opts
        self.bgimg = PhotoImage(file=os.path.join(absdir, 'RCCLabFluidic.png'))
        limg = Label(self.root, i=self.bgimg)
        limg.pack(side=TOP)
        self.root.title("RCCLab EGaIn Data Parser")
        # self.root.geometry('800x850+250+250')
        self.pack(fill=BOTH)
        self.__createWidgets()
        self.checkOptions()
        self.ToFront()

    def ToFront(self):
        '''Try to bring the main window to the front on different platforms'''
        if platform.system() == "Darwin":
            os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
        else:
            self.master.attributes('-topmost', 1)
            self.master.attributes('-topmost', 0)
        self.master.lift()

    def __createWidgets(self):
        measdone = BooleanVar(value=False)
        self.variabels['measdone'] = measdone
        busy = BooleanVar(value=False)
        self.variabels['busy'] = busy

        dataFrame = tk.Frame(self)
        controlsFrame = tk.Frame(self)
        measurementFrame = MeasurementControl(controlsFrame,
                                              measdone=measdone,
                                              busy=busy)
        self.widgets['measurementFrame'] = measurementFrame
        stagecontrolFrame = tk.LabelFrame(controlsFrame, text='Stage Controls')
        stagecontroller = StageControls(stagecontrolFrame, busy=busy)
        self.widgets['stagecontroller'] = stagecontroller
        tempcontrolFrame = tk.LabelFrame(controlsFrame, text='Temperature Controls')
        tempcontrols = TempControl(tempcontrolFrame)
        self.widgets['tempcontrols'] = tempcontrols
        # self.stagecontrolFrame.createWidgets()
        optionsFrame = tk.Frame(self)
        outputfilenameFrame = tk.Frame(optionsFrame)
        buttonFrame = tk.Frame(self)

        dataplot = dataCanvas(dataFrame)
        self.widgets['dataplot'] = dataplot

        statusFrame = tk.Frame(controlsFrame)
        sattusLabelprefix = Label(master=statusFrame, text="Status: ")
        statusVar = StringVar(value='Not Initialized')
        statusLabel = Label(master=statusFrame,
                            textvariable=statusVar)
        self.variabels['statusVar'] = statusVar

        outputfilenameEntryLabel = Label(master=outputfilenameFrame,
                                         text='Output Filename Prefix:')
        outputfilenameEntryLabel.pack(side=LEFT)
        outputfilenameEntry = Entry(master=outputfilenameFrame,
                                    width=20,
                                    font=Font(size=10))
        outputfilenameEntry.pack(side=LEFT)
        outputfilenameEntry.delete(0, END)
        outputfilenameEntry.insert(0, self.opts.output_file_name)
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            outputfilenameEntry.bind(_ev, self.checkOutputfilename)

        saveButton = tk.Button(master=buttonFrame, text="Save To", command=self.SpawnSaveDialogClick)
        saveButton.pack(side=LEFT)
        measButton = tk.Button(master=buttonFrame, text="Measure",
                               command=measurementFrame.startMeasurementButtonClick)
        self.widgets['measButton'] = measButton
        measButton.pack(side=LEFT)
        measButton['state'] = DISABLED
        measButton.after(100, self.checkOptions)
        quitButton = tk.Button(master=buttonFrame, text="Quit", command=self.quitButtonClick)
        self.widgets['quitButton'] = quitButton

        measdone.trace_add('write', self._updateData)
        busy.trace_add('write', self._checkbusy)

        quitButton.pack(side=BOTTOM)

        dataFrame.pack(side=TOP, fill=BOTH)
        measurementFrame.pack(side=TOP, fill=BOTH)
        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        sattusLabelprefix.pack(side=LEFT)
        statusLabel.pack(side=LEFT)
        statusFrame.pack(side=BOTTOM)
        controlsFrame.pack(side=TOP)
        stagecontrolFrame.pack(side=LEFT)
        tempcontrolFrame.pack(side=LEFT)
        stagecontroller.pack(side=LEFT, fill=Y)
        tempcontrols.pack(side=RIGHT, fill=Y)
        outputfilenameFrame.pack(side=BOTTOM, fill=BOTH)
        optionsFrame.pack(side=BOTTOM, fill=Y)
        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        buttonFrame.pack(side=BOTTOM, fill=X)

    def quitButtonClick(self):
        self.widgets['quitButton']['state'] = DISABLED
        self.variabels['statusVar'].set('Shutting down')
        self.__quit()

    def __quit(self):
        self.widgets['tempcontrols'].shutdown()
        self.widgets['stagecontroller'].shutdown()
        time.sleep(1)
        self.root.quit()

    def SpawnSaveDialogClick(self):
        self.checkOptions()
        self.opts.save_path += filedialog.askdirectory(
            title="Path to save data",
            initialdir=self.opts.save_path)

    def checkOutputfilename(self, event):
        self.opts.output_file_name = event.widget.get()
        self.checkOptions()

    def checkOptions(self):
        _initialized = False
        for _widget in 'measurementFrame', 'stagecontroller':
            _initialized = self.widgets[_widget].initialized
        if _initialized:
            self.widgets['measButton']['state'] = NORMAL
            self.variabels['statusVar'].set('Initialized')
        else:
            self.widgets['measButton'].after(100, self.checkOptions)
        # print(self.opts)
        # self.outputfilenameEntry.delete(0, END)
        # self.outputfilenameEntry.insert(0, self.opts.output_file_name)

    def _updateData(self, *args):
        self.variabels['measdone'].set(False)
        self.widgets['dataplot']({'x':[1,2,3], 'y':[4,5,6]})

    def _checkbusy(self, *args):
        if self.variabels['busy'].get():
            self.widgets['quitButton']['state'] = DISABLED
            self.widgets['measButton'] = DISABLED
        else:
            self.widgets['quitButton']['state'] = NORMAL
            self.widgets['measButton'] = NORMAL
