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
import math
import csv
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

JUNCTION_CONVERSION_FACTOR = 0.1  # cm/cm
MEASURING = 'Measuring'
READY = 'Ready'
NOT_INITIALIZED = 'Not initalized'
csv.register_dialect('JV', delimiter='\t', quoting=csv.QUOTE_MINIMAL)

class MainFrame(tk.Frame):
    '''The main frame for collecting EGaIn data.'''

    widgets = {}
    variables = {}
    junction_size = 1.0
    initialized = False

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
        self.variables['measdone'] = measdone
        busy = BooleanVar(value=False)
        self.variables['busy'] = busy

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
        optionsFrame = tk.Frame(self)
        # outputfilenameFrame = tk.Frame(optionsFrame)
        buttonFrame = tk.Frame(self)

        dataplot = dataCanvas(dataFrame)
        self.widgets['dataplot'] = dataplot

        statusFrame = tk.Frame(controlsFrame)
        sattusLabelprefix = Label(master=statusFrame, text="Status: ")
        statusVar = StringVar(value=NOT_INITIALIZED)
        statusLabel = Label(master=statusFrame,
                            textvariable=statusVar)
        self.variables['statusVar'] = statusVar

        outputfilenameEntryLabel = Label(master=optionsFrame,
                                         text='Output Filename Prefix:')
        outputfilenameEntryLabel.pack(side=LEFT)
        outputfilenameEntry = Entry(master=optionsFrame,
                                    width=20,
                                    font=Font(size=10))
        outputfilenameEntry.pack(side=LEFT)
        outputfilenameEntry.delete(0, END)
        outputfilenameEntry.insert(0, self.opts.output_file_name)
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            outputfilenameEntry.bind(_ev, self.checkOutputfilename)
        junctionsizeEntryLabel = Label(master=optionsFrame,
                                       text='Junction size (cm):')
        junctionsizeEntryLabel.pack(side=LEFT)
        junctionsizeEntry = Entry(master=optionsFrame,
                                  width=5,
                                  font=Font(size=10))
        junctionsizeEntry.pack(side=LEFT)
        junctionsizeEntry.delete(0, END)
        junctionsizeEntry.insert(0, self.junction_size)
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            junctionsizeEntry.bind(_ev, self.checkJunctionsize)

        saveButton = tk.Button(master=buttonFrame, text="Save To", command=self.SpawnSaveDialogClick)
        saveButton.pack(side=LEFT)
        measButton = tk.Button(master=buttonFrame, text="Measure",
                               command=measurementFrame.startMeasurementButtonClick)
        self.widgets['measButton'] = measButton
        measButton.pack(side=LEFT)
        measButton['state'] = DISABLED
        measButton.after(100, self.checkOptions)
        stopButton = tk.Button(master=buttonFrame, text='Stop',
                               command=measurementFrame.stop_measurement)
        self.widgets['stopButton'] = stopButton
        stopButton.pack(side=LEFT)
        quitButton = tk.Button(master=buttonFrame, text="Quit", command=self.quitButtonClick)
        self.widgets['quitButton'] = quitButton

        measdone.trace_add('write', self._updateData)
        measdone.trace_add(('read', 'write'), self._checkbusy)
        busy.trace_add(('read', 'write'), self._checkbusy)

        quitButton.pack(side=BOTTOM)

        dataFrame.pack(side=TOP, fill=BOTH)
        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        optionsFrame.pack(side=TOP, fill=X)
        # outputfilenameFrame.pack(side=BOTTOM, fill=BOTH)
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

        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        buttonFrame.pack(side=BOTTOM, fill=X)

    def quitButtonClick(self):
        self.widgets['quitButton']['state'] = DISABLED
        self.variables['statusVar'].set('Shutting down')
        self.__quit()

    def __quit(self):
        self.widgets['measurementFrame'].shutdown()
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

    def checkJunctionsize(self, event):
        _junction_size = event.widget.get()
        if not _junction_size:
            return
        try:
            self.junction_size = float(_junction_size)
        except ValueError:
            event.widget.delete(0, END)
            event.widget.insert(0, self.junction_size)

    def checkOptions(self):
        if self.variables['statusVar'].get() in (MEASURING, READY):
            self.widgets['measButton'].after(100, self.checkOptions)
            return
        _initialized = [False, False, False]
        _connected = []
        if self.widgets['measurementFrame'].initialized:
            _connected.append('SMU')
            _initialized[0] = True
        if self.widgets['stagecontroller'].initialized:
            _connected.append('Stage')
            _initialized[1] = True
        if self.widgets['tempcontrols'].initialized:
            _connected.append('Peltier')
            _initialized[2] = True
        if len(_connected) > 1:
            _connected = _connected[:-1]+['and', _connected[-1]]
        if True in _initialized:
            self.widgets['measButton']['state'] = NORMAL
            self.variables['statusVar'].set(" ".join(_connected)+" connected")
            self.initialized = True
        else:
            self.variables['statusVar'].set('Not Initialized')
        if False in _initialized and not self.variables['busy'].get():
            self.widgets['measButton'].after(100, self.checkOptions)

    def _updateData(self, *args):
        if self.variables['measdone'].get():
            results = self.widgets['measurementFrame'].data
            if len(results['V']) == len(results['I']):
                self.widgets['dataplot'].displayData(results)
            self._writedata(False)
            # self.widgets['dataplot'].displayData({'x':[1,2,3], 'y':[4,5,6]})
        if not self.variables['busy'].get():
            self._writedata(True)

    def _writedata(self, finalize=False):
        # Save data to disk and then delete them
        # DATA_FORMAT = {'V':[], 'I':[], 'R':[], 't':[], 's':[]}
        _area = math.pi*(self.junction_size * JUNCTION_CONVERSION_FACTOR)**2
        results = self.widgets['measurementFrame'].data
        results['J'] = []
        for _I in results['I']:
            results['J'].append(_I/_area)
        _fn = os.path.join(self.opts.save_path, self.opts.output_file_name)
        if finalize:
            write_data_to_file(f'{_fn}.txt', results)
            try:
                os.remove(f'{_fn}_temp.txt')
            except FileNotFoundError:
                pass
            del self.widgets['measurementFrame'].data
        else:
            write_data_to_file(f'{_fn}_temp.txt', results)

    def _checkbusy(self, *args):
        if not self.initialized:
            return
        if self.variables['busy'].get():
            self.variables['statusVar'].set(f"{MEASURING} sweep {self.widgets['measurementFrame'].sweeps_done+1}")
        else:
            self.variables['statusVar'].set(READY)
        if self.variables['busy'].get():
            self.widgets['quitButton']['state'] = DISABLED
            self.widgets['measButton']['state'] = DISABLED
        else:
            self.widgets['quitButton']['state'] = NORMAL
            self.widgets['measButton']['state'] = NORMAL

def write_data_to_file(fn, results):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='JV')
        writer.writerow(['V (V)', 'I (A)', 'J (A/cm2)', 'Time (s)'])
        for _idx, V in enumerate(results['V']):
            writer.writerow([V,
                             results['I'][_idx],
                             results['J'][_idx],
                             results['t'][_idx]])
