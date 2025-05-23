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
import csv
from pathlib import Path
import tkinter.ttk as tk
from tkinter import filedialog
from tkinter import StringVar, BooleanVar, Label, Entry, messagebox
from tkinter import X, Y
from tkinter import TOP, BOTTOM, LEFT, RIGHT
from tkinter import END, BOTH, HORIZONTAL
from tkinter import DISABLED, NORMAL
from tkinter import PhotoImage
from tkinter.font import Font
from egain.tk_gui.util import parseusersettings
from egain.config.options import GLOBAL_OPTS, createOptions
from egain.tk_gui.datacanvas import dataCanvas
from egain.tk_gui.seebeck.tempcontrol import TempControl
from egain.tk_gui.seebeck.seebeckmeas import SeebeckMeas

absdir = os.path.dirname(os.path.realpath(__file__))

JUNCTION_CONVERSION_FACTOR = 0.1  # cm/cm
MEASURING = 'Measuring'
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
    vt_data = {'V':[], 'leftT':[], 'rightT':[], 'time':[]}
    measuring = False
    timer = 0
    config_file = GLOBAL_OPTS

    def __init__(self, root, cli_opts=None):
        self.root = root
        super().__init__(self.root)
        self.opts = createOptions()
        self.bgimg = PhotoImage(file=os.path.join(absdir, 'RCCLabFluidic.png'))
        limg = Label(self.root, i=self.bgimg)
        limg.pack(side=TOP)
        self.root.title("RCCLab Thermoelectric Controller")
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
        busy = BooleanVar(value=False)
        self.variables['busy'] = busy
        dataFrame = tk.Frame(self)
        controlsFrame = tk.Frame(self)
        controlsFrameWest = tk.LabelFrame(controlsFrame, text='Seebeck Measurements')
        controlsFrameEast = tk.LabelFrame(controlsFrame, text='Temperature Gradient Controls')
        # controlsFrameSouth = tk.Frame(controlsFrame)
        seebeckmeasFrame = SeebeckMeas(controlsFrameWest)
        self.widgets['seebeckmeasFrame'] = seebeckmeasFrame
        # voltmeterFrame = tk.LabelFrame(controlsFrameWest, text='Voltmeter Controls')
        # voltmetercontrols = MeasurementReadV(voltmeterFrame, busy=busy)
        # self.widgets['voltmetercontrols'] = voltmetercontrols
        # tempcontrolFrame = tk.LabelFrame(controlsFrameEast, text='Temperature Gradient Controls')
        tempcontrols = TempControl(controlsFrameEast)
        self.widgets['tempcontrols'] = tempcontrols
        optionsFrame = tk.Frame(self)
        outputFrame = tk.Frame(optionsFrame)
        buttonFrame = tk.Frame(self)
        statusFrame = tk.Frame(self)

        dataplot = dataCanvas(dataFrame, xlabel='ΔT (K)', ylabel='Thermovoltage (mV)')
        self.widgets['dataplot'] = dataplot

        sattusLabelprefix = Label(master=statusFrame, text="Status: ")
        statusVar = StringVar(value=NOT_INITIALIZED)
        statusLabel = Label(master=statusFrame,
                            textvariable=statusVar)
        self.variables['statusVar'] = statusVar

        outputfilenameEntryLabel = Label(master=outputFrame,
                                         text='Output Filename Prefix:')
        outputfilenameEntryLabel.pack(side=LEFT)
        outputdirstring = StringVar(value=self.opts['save_path'])
        self.variables['outputdirstring'] = outputdirstring
        outputdirLabel = Label(master=outputFrame,
                               textvariable=outputdirstring)
        outputfilenameEntry = Entry(master=outputFrame,
                                    width=20,
                                    font=Font(size=10))
        self.widgets['outputfilenameEntry'] = outputfilenameEntry
        outputdirLabel.pack(side=LEFT)
        outputfilenameEntry.pack(side=LEFT)
        outputfilenameEntry.delete(0, END)
        outputfilenameEntry.insert(0, self.opts['output_file_name'])
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            outputfilenameEntry.bind(_ev, self.checkOutputfilename)
        self.widgets['outputfilenameEntry'] = outputfilenameEntry

        outputFrame.pack(side=TOP, fill=X)
        saveButton = tk.Button(master=buttonFrame, text="Save To", command=self.SpawnSaveDialogClick)
        saveButton.pack(side=LEFT)
        measButton = tk.Button(master=buttonFrame, text="Measure",
                               command=self.measButtonClick)
        self.widgets['measButton'] = measButton
        measButton.pack(side=LEFT)
        measButton['state'] = DISABLED
        measButton.after(100, self.checkOptions)
        stopButton = tk.Button(master=buttonFrame, text='Stop',
                               command=self.stopbuttonclick)
        self.widgets['stopButton'] = stopButton
        stopButton.pack(side=LEFT)
        quitButton = tk.Button(master=buttonFrame, text="Quit", command=self.quitButtonClick)
        self.widgets['quitButton'] = quitButton

        quitButton.pack(side=BOTTOM)
        dataFrame.pack(side=TOP, fill=BOTH)
        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        optionsFrame.pack(side=TOP, fill=X)
        tk.Separator(self, orient=HORIZONTAL).pack(fill=X)
        sattusLabelprefix.pack(side=LEFT)
        statusLabel.pack(side=LEFT)
        controlsFrame.pack(side=TOP, fill=Y)
        controlsFrameWest.pack(side=LEFT, fill=Y)
        controlsFrameEast.pack(side=LEFT, fill=Y)
        seebeckmeasFrame.pack(side=TOP)
        # voltmeterFrame.pack(side=TOP)
        # voltmetercontrols.pack(side=LEFT, fill=Y)
        tempcontrols.pack(side=RIGHT, fill=Y)
        tk.Separator(controlsFrame, orient=HORIZONTAL).pack(side=TOP, fill=X)
        statusFrame.pack(side=BOTTOM)
        buttonFrame.pack(side=BOTTOM, fill=X)

    def quitButtonClick(self):
        self.widgets['quitButton']['state'] = DISABLED
        self.variables['statusVar'].set('Shutting down')
        self.__quit()

    def __quit(self):
        # self.widgets['voltmetercontrols'].shutdown()
        self.widgets['tempcontrols'].shutdown()
        time.sleep(1)
        self.root.quit()

    def _record(self, *args):
        if not self.measuring:
            return
        self.vt_data['V'].append(self.widgets['seebeckmeasFrame'].voltage)
        self.vt_data['leftT'].append(self.widgets['seebeckmeasFrame'].temps['left'])
        self.vt_data['rightT'].append(self.widgets['seebeckmeasFrame'].temps['right'])
        _dt = time.time() - self.timer
        self.vt_data['time'].append(_dt)
        self.widgets['measButton'].configure(text=f'Recording {_dt:.0f}')
        self._writedata()
        self._updateData()
        self.widgets['measButton'].after(500, self._record)

    def measButtonClick(self):
        self.measuring = not self.measuring
        if self.measuring:
            self.timer = time.time()
            self.vt_data = {'V':[], 'leftT':[], 'rightT':[], 'time':[]}
            self.widgets['measButton'].configure(text='Recording 0')
        else:
            self.widgets['measButton'].configure(text='Measure')
            self._writedata(finalize=True)
        self._record()

    def stopbuttonclick(self):
        self.measuring = True
        self.measButtonClick()

    def SpawnSaveDialogClick(self):
        _path = filedialog.askdirectory(
            title="Path to save data",
            initialdir=self.opts['save_path'])
        if not _path:
            return
        self.opts['save_path'] = Path(_path)
        logger.debug(f"Saving to {self.opts['save_path']}")
        self.variables['outputdirstring'].set(self.opts['save_path'])
        self.checkOptions()

    def checkOutputfilename(self, event):
        self.opts['output_file_name'] = event.widget.get()
        if os.path.exists(os.path.join(self.variables['outputdirstring'].get(),
                          f"{event.widget.get()}_data.txt")):
            event.widget.config({"background": "Yellow"})
        else:
            event.widget.config({"background": "White"})
        self.checkOptions()

    def checkOptions(self, *args):
        self.opts['output_file_name'] = self.widgets['outputfilenameEntry'].get()
        _outdir = f"/{self.variables['outputdirstring'].get().strip('/')}/"
        self.variables['outputdirstring'].set(_outdir)
        if self.variables['statusVar'].get() in (MEASURING):
            self.widgets['measButton'].after(100, self.checkOptions)
            return
        _initialized = [False, False]
        _connected = []
        if self.widgets['tempcontrols'].initialized:
            _connected.append('Peltier')
            _initialized[0] = True
        if self.widgets['seebeckmeasFrame'].initialized:
            _connected.append('Seebeck Meas')
            _initialized[1] = True
        if len(_connected) > 1:
            _connected = _connected[:-1]+['and', _connected[-1]]
        if _initialized[1] is True:
            self.widgets['measButton']['state'] = NORMAL
        if False in _initialized and not self.variables['busy'].get():
            self.widgets['measButton'].after(100, self.checkOptions)
        if True in _initialized:
            self.variables['statusVar'].set(" ".join(_connected)+" connected")
            self.initialized = True
        else:
            self.variables['statusVar'].set('Not Initialized')
        parseusersettings(self.config_file, self.opts)

    def _updateData(self, *args):
        results = {'V':[], 'DT':[]}
        for _v in self.vt_data['V']:
            results['V'].append(_v*1000)
        _lt = self.vt_data['leftT']
        _rt = self.vt_data['rightT']
        for i in range(len(_lt)):
            results['DT'].append(_lt[i] - _rt[i])
        self.widgets['dataplot'].displayData(results, xlabel='Δ (K)', ylabel='Thermovoltage (mV)', xkey='DT', ykey='V')

    def _writedata(self, finalize=False):
        if not self.vt_data['V']:
            return
        self.checkOptions()
        _fn = os.path.join(self.opts['save_path'], self.opts['output_file_name'])
        if finalize:
            if os.path.exists(_fn):
                if not tk.askyesno("Overwrite?", f'{_fn} exists, overwrite it?'):
                    _fn = f'{_fn}_{str(self.counter).zfill(2)}'
                    self.counter += 1
            write_data_to_file(f'{_fn}_data.txt', self.vt_data)
            try:
                os.remove(f'{_fn}_tmp.txt')
            except FileNotFoundError:
                pass
            self.vt_data = {'V':[], 'leftT':[], 'rightT':[], 'time':[]}
            messagebox.showinfo("Saved", f"Data written to {_fn}_data.txt")
        else:
            write_data_to_file(f'{_fn}_tmp.txt', self.vt_data)

def write_data_to_file(fn, results):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='JV')
        writer.writerow(['V (V)', 'Left T (°C)', 'Rigth T (°C)', 'Delta Time (s)', 'L-R Temp (°C)'])
        for _idx, V in enumerate(results['V']):
            writer.writerow([V,
                             results['leftT'][_idx],
                             results['rightT'][_idx],
                             f"{results['time'][_idx]:0.2f}",
                             results['leftT'][_idx] - results['rightT'][_idx]])
