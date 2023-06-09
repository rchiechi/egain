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
# import datetime
# import logging
# import threading
import tkinter.ttk as tk
# from tkinter import Tk
# from tkinter import Toplevel
from tkinter import Toplevel, filedialog
from tkinter import StringVar, BooleanVar, Label, Entry, messagebox
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, HORIZONTAL  # pylint: disable=unused-import
from tkinter import DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
# from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
from gui.datacanvas import dataCanvas
from gui.stagecontrol import StageControls
from gui.tempcontrol import TempControl
from gui.measurement import MeasurementControl

absdir = os.path.dirname(os.path.realpath(__file__))

REFERENCE_SIZE_M = 450e-6  # Standard syringe barrel is 450 µm
# JUNCTION_CONVERSION_FACTOR = 0.1  # cm/cm
MEASURING = 'Measuring'
MOVING = 'Stage in motion'
READY = 'Ready'
NOT_INITIALIZED = 'Not initalized'
INITIALIZED = 'Initialized'
STRFTIME = '%Y-%m-%dT%H:%M:%SZ'
csv.register_dialect('JV', delimiter='\t', quoting=csv.QUOTE_MINIMAL)

class MainFrame(tk.Frame):
    '''The main frame for collecting EGaIn data.'''

    widgets = {}
    variables = {}
    initialized = False
    counter = 0

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
        outputFrame = tk.Frame(optionsFrame)
        magFrame = tk.Frame(optionsFrame)
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

        outputfilenameEntryLabel = Label(master=outputFrame,
                                         text='Output Filename Prefix:')
        outputfilenameEntryLabel.pack(side=LEFT)
        outputdirstring = StringVar(value=self.opts.save_path+'/')
        self.variables['outputdirstring'] = outputdirstring
        outputdirLabel = Label(master=outputFrame,
                               textvariable=outputdirstring)
        outputfilenameEntry = Entry(master=outputFrame,
                                    width=20,
                                    font=Font(size=10))
        outputdirLabel.pack(side=LEFT)
        outputfilenameEntry.pack(side=LEFT)
        outputfilenameEntry.delete(0, END)
        outputfilenameEntry.insert(0, self.opts.output_file_name)
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            outputfilenameEntry.bind(_ev, self.checkOutputfilename)
        maketipButton = tk.Button(master=magFrame,
                                  text='Make Tip',
                                  command=self.maketipButtonClick,
                                  state=DISABLED)
        self.widgets['maketipButton'] = maketipButton
        maketipButton.pack(side=LEFT)

        referencesizeEntryLabel = Label(master=magFrame,
                                        text='Reference size (cm):')
        referencesizeEntryLabel.pack(side=LEFT)
        reference_size = StringVar(value='5.0')
        self.variables['reference_size'] = reference_size
        referencesizeEntry = Entry(master=magFrame,
                                   width=5,
                                   textvariable=reference_size,
                                   font=Font(size=10))
        referencesizeEntry.pack(side=LEFT)

        junctionsizeEntryLabel = Label(master=magFrame,
                                       text='Junction size (cm):')
        junctionsizeEntryLabel.pack(side=LEFT)
        junction_size = StringVar(value='1.0')
        self.variables['junction_size'] = junction_size
        junctionsizeEntry = Entry(master=magFrame,
                                  width=5,
                                  textvariable=junction_size,
                                  font=Font(size=10))
        junctionsizeEntry.pack(side=LEFT)

        junctionmagEntryLabel = Label(master=magFrame,
                                      text='Magnification:')
        junctionmagEntryLabel.pack(side=LEFT)
        junction_mag = StringVar(value='2.5')
        self.variables['junction_mag'] = junction_mag
        junctionmag = tk.Spinbox(magFrame,
                                 font=Font(size=10),
                                 from_=1,
                                 to=20,
                                 increment=0.5,
                                 textvariable=junction_mag,
                                 width=4)
        junctionmag.pack(side=LEFT)

        outputFrame.pack(side=TOP, fill=X)
        magFrame.pack(side=TOP, fill=X)

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

    def maketipButtonClick(self):
        _t = 0
        _alive, _res = self.widgets['measurementFrame'].getResistanceReader()
        _meas = _res.read().split(b'\r')[0]
        try:
            ohms = float(_meas)
        except ValueError:
            ohms = 1000000.0
        if ohms > 200:  # 20Ω is compliance
            messagebox.showerror("Error", "No tip contact.")
            _alive.clear()
            return
        self.widgets['stagecontroller'].raiseZaxis()
        time.sleep(0.1)
        while self.widgets['stagecontroller'].isbusy:
            try:
                ohms = float(_meas)
            except ValueError:
                ohms = 1000000.0
            print(f"Measured {ohms:0.1f}Ω")
            if ohms > 100:
                print("Resistance > 100Ω --> tip formed?")
                break
            _t += 1
            print(_t)
            if _t > 120:
                break
            time.sleep(0.1)
        self.widgets['stagecontroller'].stopZaxis()
        _alive.clear()
        self.widgets['quitButton']['state'] = NORMAL
        messagebox.showinfo("Tip", "I think I made a tip..?")

    def SpawnSaveDialogClick(self):
        self.opts.save_path = filedialog.askdirectory(
            title="Path to save data",
            initialdir=self.opts.save_path)
        self.variables['outputdirstring'].set(self.opts.save_path)
        self.checkOptions()

    def checkOutputfilename(self, event):
        self.opts.output_file_name = event.widget.get()
        self.checkOptions()

    def checkJunctionsize(self, event):
        _junction_size = self.variables['junction_size'].get()
        if not _junction_size:
            return
        try:
            float(_junction_size)
        except ValueError:
            self.variables['junction_size'].set('1.0')

    def checkOptions(self, *args):
        _outdir = f"/{self.variables['outputdirstring'].get().strip('/')}/"
        self.variables['outputdirstring'].set(_outdir)
        if self.variables['statusVar'].get() in (MEASURING):
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
        if _initialized[0] is True:
            self.widgets['measButton']['state'] = NORMAL
            self.variables['statusVar'].set(" ".join(_connected)+" connected")
        else:
            self.variables['statusVar'].set('Not Initialized')
        if _initialized[0] is True and _initialized[1] is True:
            self.widgets['maketipButton']['state'] = NORMAL
        if False in _initialized and not self.variables['busy'].get():
            self.widgets['measButton'].after(100, self.checkOptions)
        if True in _initialized:
            self.initialized = True

    def _updateData(self, *args):
        if self.variables['measdone'].get():
            results = self.widgets['measurementFrame'].data
            if len(results['V']) == len(results['I']):
                self.widgets['dataplot'].displayData(results)
            self._writedata(False)
            # self.widgets['dataplot'].displayData({'x':[1,2,3], 'y':[4,5,6]})
        # if not self.variables['busy'].get():
        if not self.widgets['measurementFrame'].isbusy:
            self._writedata(True)
            # print(">>>>>>>>>>>> _updateData Measurement is not busy")

    def _writedata(self, finalize=False):
        # TEMPERATURE DATA!!!
        # Save data to disk and then delete them
        # DATA_FORMAT = {'V':[], 'I':[], 't':[]}
        self.checkOptions()
        _jsize = float(self.variables['junction_size'].get())
        _rsize = float(self.variables['reference_size'].get())  # screen_cm
        # _jmag = float(self.variables['junction_mag'].get())
        _conversion = (REFERENCE_SIZE_M * 100) / _rsize  # (m cm/m) / screen_cm = cm / screen_cm
        _area_in_cm = math.pi*(_conversion * _jsize)**2  # pi((cm / screen_cm) screen_cm) = cm
        results = self.widgets['measurementFrame'].data
        for _key in ('J', 'upper', 'lower'):
            results[_key] = []
        for _I in results['I']:
            results['J'].append(_I/_area_in_cm)
            results['upper'].append(self.widgets['tempcontrols'].uppertemp)
            results['lower'].append(self.widgets['tempcontrols'].lowertemp)
        _fn = os.path.join(self.opts.save_path, self.opts.output_file_name)
        if finalize:
            if os.path.exists(_fn):
                if not tk.askyesno("Overwrite?", f'{_fn} exists, overwrite it?'):
                    _fn = f'{_fn}_{str(self.counter).zfill(2)}'
                    self.counter += 1
            write_data_to_file(f'{_fn}_data.txt', results)
            try:
                os.remove(f'{_fn}_tmp.txt')
            except FileNotFoundError:
                pass
            del self.widgets['measurementFrame'].data
        else:
            write_data_to_file(f'{_fn}_tmp.txt', results)

        with open(f'{_fn}_metadata.txt', 'w') as fh:
            fh.write(f'{time.strftime(STRFTIME)}\n')
            fh.write(f'Onscreen junction size:{_jsize}\n')
            fh.write(f"Magnification:{self.variables['junction_mag'].get()}\n")
            fh.write(f'Junction conversion factor:{_conversion}\n')
            fh.write(f"Peltier enabled: {self.widgets['tempcontrols'].peltierstatus}\n")
            fh.write(f"Upper temperature (°C): {self.widgets['tempcontrols'].uppertemp}\n")
            fh.write(f"Lower temperature (°C): {self.widgets['tempcontrols'].lowertemp}\n")
        if finalize:
            messagebox.showinfo("Saved", f"Data written to {_fn}_data.txt")

    def _checkbusy(self, *args):
        if not self.initialized:
            return
        if self.variables['busy'].get():
            if self.widgets['stagecontroller'].isbusy:
                self.variables['statusVar'].set(f"{MOVING}")
            if self.widgets['measurementFrame'].isbusy:
                self.variables['statusVar'].set(
                    f"{MEASURING} sweep {self.widgets['measurementFrame'].sweeps_done+1}")
        else:
            self.variables['statusVar'].set(READY)
        # if self.variables['busy'].get():
        if self.widgets['measurementFrame'].isbusy or self.variables['busy'].get():
            self.widgets['quitButton']['state'] = DISABLED
            self.widgets['measButton']['state'] = DISABLED
            # self.widgets['measurementFrame'].after(100, self._checkbusy)
            # print(f">>>> _checkbusy Measurement Frame is busy {self.widgets['measurementFrame'].isbusy}, {self.variables['busy'].get()}")
        else:
            self.widgets['quitButton']['state'] = NORMAL
            self.widgets['measButton']['state'] = NORMAL


def write_data_to_file(fn, results):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='JV')
        writer.writerow(['V (V)', 'I (A)', 'J (A/cm2)', 'Time (s)', 'Upper Temp (°C)', 'Lower Temp (°C)'])
        for _idx, V in enumerate(results['V']):
            writer.writerow([V,
                             results['I'][_idx],
                             results['J'][_idx],
                             results['t'][_idx],
                             results['upper'][_idx],
                             results['lower'][_idx]])


def maketip(smu, stage):
    popup = Toplevel()
    popup.geometry('500x100+250-250')
    _msg = StringVar()
    Label(popup, textvariable=_msg).pack()