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
from pathlib import Path
import logging
import tkinter.ttk as tk
from tkinter import Toplevel, filedialog
from tkinter import StringVar, IntVar, BooleanVar, Label, Entry, messagebox, Checkbutton
from tkinter import X, Y
from tkinter import TOP, BOTTOM, LEFT, RIGHT
from tkinter import END, BOTH, HORIZONTAL
from tkinter import DISABLED, NORMAL
from tkinter import PhotoImage
from tkinter.font import Font
from egain.tk_gui.datacanvas import dataCanvas
from egain.tk_gui.stagecontrol import StageControls
from egain.tk_gui.egain.tempcontrol import TempControl
from egain.tk_gui.egain.measurement import MeasurementControl
from egain.tk_gui.tooltip import CreateTooltip
from egain.tk_gui.util import parseusersettings
from egain.config.options import GLOBAL_OPTS, createOptions

absdir = os.path.dirname(os.path.realpath(__file__))

# REFERENCE_SIZE_M = 450e-6  # Standard syringe barrel is 450 µm
REFERENCE_SIZE_M = 250e-6  # Standard syringe barrel is 250 µm

# JUNCTION_CONVERSION_FACTOR = 0.1  # cm/cm
MEASURING = 'Measuring'
MOVING = 'Stage in motion'
READY = 'Ready'
NOT_INITIALIZED = 'Not initalized'
INITIALIZED = 'Initialized'
STRFTIME = '%Y-%m-%dT%H:%M:%SZ'
csv.register_dialect('JV', delimiter='\t', quoting=csv.QUOTE_MINIMAL)

logger = logging.getLogger(__package__+'.main')

class MainFrame(tk.Frame):
    '''The main frame for collecting EGaIn data.'''

    widgets = {}
    egain_widgets = []
    afm_widgets = []
    variables = {}
    initialized = False
    counter = 0
    config_file = GLOBAL_OPTS

    def __init__(self, root, cli_opts):
        self.root = root
        super().__init__(self.root)
        self.cli_opts = cli_opts
        self.opts = createOptions()
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
        sweepdone = BooleanVar(value=False)
        self.variables['sweepdone'] = sweepdone
        busy = BooleanVar(value=False)
        self.variables['busy'] = busy

        dataFrame = tk.Frame(self)
        controlsFrame = tk.Frame(self)
        measurementFrame = MeasurementControl(controlsFrame,
                                              self.cli_opts,
                                              sweepdone=sweepdone,
                                              busy=busy)
        self.widgets['measurementFrame'] = measurementFrame
        stagecontrolFrame = tk.LabelFrame(controlsFrame, text='Stage Controls')
        stagecontroller = StageControls(stagecontrolFrame, busy=busy)
        self.widgets['stagecontroller'] = stagecontroller
        self.egain_widgets.append('stagecontroller')
        tempcontrolFrame = tk.LabelFrame(controlsFrame, text='Temperature Controls')
        tempcontrols = TempControl(tempcontrolFrame)
        self.widgets['tempcontrols'] = tempcontrols
        self.egain_widgets.append('tempcontrols')
        optionsFrame = tk.Frame(self)
        outputFrame = tk.Frame(optionsFrame)

        magFrame = tk.LabelFrame(optionsFrame, text='EGaIn Tip Geometry')
        afmFrame = tk.LabelFrame(optionsFrame, text='AFM Tip Geometry')
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
        outputdirstring = StringVar(value=self.opts['save_path'])
        self.variables['outputdirstring'] = outputdirstring
        outputdirLabel = Label(master=outputFrame,
                               textvariable=outputdirstring)
        outputfilenameEntry = Entry(master=outputFrame,
                                    width=20,
                                    font=Font(size=10))
        outputdirLabel.pack(side=LEFT)
        outputfilenameEntry.pack(side=LEFT)
        outputfilenameEntry.delete(0, END)
        outputfilenameEntry.insert(0, self.opts['output_file_name'])
        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            outputfilenameEntry.bind(_ev, self.checkOutputfilename)
        self.widgets['outputfilenameEntry'] = outputfilenameEntry

        makejunctionButton = tk.Button(master=magFrame,
                                       text='Make Junction',
                                       command=self.makejunctionButtonClick,
                                       state=DISABLED)
        self.widgets['makejunctionButton'] = makejunctionButton
        makejunctionButton.pack(side=LEFT)
        # EGaIn-specific widgets
        referencesizeEntryLabel = Label(master=magFrame,
                                        text='Reference size (cm):')
        referencesizeEntryLabel.pack(side=LEFT)
        reference_size = StringVar(value='5.0')
        self.variables['reference_size'] = reference_size
        self.widgets['referencesizeEntry'] = Entry(master=magFrame,
                                                   width=5,
                                                   textvariable=reference_size,
                                                   font=Font(size=10))
        self.egain_widgets.append('referencesizeEntry')
        self.widgets['referencesizeEntry'].pack(side=LEFT)
        CreateTooltip(self.widgets['referencesizeEntry'], "Size of a reference object on screen")
        junctionsizeEntryLabel = Label(master=magFrame,
                                       text='Junction size (cm):')
        junctionsizeEntryLabel.pack(side=LEFT)
        junction_size = StringVar(value='1.0')
        self.variables['junction_size'] = junction_size
        self.widgets['junctionsizeEntry'] = Entry(master=magFrame,
                                                  width=5,
                                                  textvariable=junction_size,
                                                  font=Font(size=10))
        self.egain_widgets.append('junctionsizeEntry')
        self.widgets['junctionsizeEntry'].pack(side=LEFT)
        CreateTooltip(self.widgets['junctionsizeEntry'], "Size of the junction on screen")

        junctionmagEntryLabel = Label(master=magFrame,
                                      text='Magnification:')
        junctionmagEntryLabel.pack(side=LEFT)
        junction_mag = StringVar(value='2.5')
        self.variables['junction_mag'] = junction_mag
        self.widgets['junctionmag'] = tk.Spinbox(magFrame,
                                                 font=Font(size=10),
                                                 from_=1,
                                                 to=20,
                                                 increment=0.5,
                                                 textvariable=junction_mag,
                                                 width=4)
        self.egain_widgets.append('junctionmag')
        self.widgets['junctionmag'].pack(side=LEFT)
        CreateTooltip(self.widgets['junctionmag'], "Magnification value on zoom lens")

        # AFM Widgets
        tipsizeEntryLabel = Label(master=afmFrame,
                                  text='Tip diameter (nm):')
        tipsizeEntryLabel.pack(side=LEFT)
        tip_size = StringVar(value='15')
        self.variables['tip_size'] = tip_size
        self.widgets['tipsizeEntry'] = Entry(master=afmFrame,
                                             width=5,
                                             textvariable=tip_size,
                                             font=Font(size=8))
        self.egain_widgets.append('tipsizeEntry')
        self.widgets['tipsizeEntry'].pack(side=LEFT)
        self.widgets['tipsizeEntry']['state'] = DISABLED
        CreateTooltip(self.widgets['tipsizeEntry'], "Diameter of the AFM tip in nm")
        self.variables['isafm'] = IntVar()
        self.variables['isafm'].set(self.opts['isafm'])
        self.variables['isafm'].trace_add('write', self._checkafm)
        afmoregainCheck = Checkbutton(afmFrame, text='AFM', variable=self.variables['isafm'])
        afmoregainCheck.pack(side=LEFT)
        # # #

        outputFrame.pack(side=TOP, fill=X)
        tk.Separator(optionsFrame, orient=HORIZONTAL).pack(fill=X)
        magFrame.pack(side=TOP, fill=X)
        afmFrame.pack(side=TOP, fill=X)

        for _ev in ('<Return>', '<Leave>', '<Enter>'):
            self.widgets['junctionsizeEntry'].bind(_ev, self.checkJunctionsize)
            self.widgets['tipsizeEntry'].bind(_ev, self.checkJunctionsize)

        self.afm_widgets.append('tipsizeEntry')
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

        sweepdone.trace_add('write', self._updateData)
        sweepdone.trace_add(('read', 'write'), self._checkbusy)
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

        self._checkafm()
        self.checkOptions()

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

    def makejunctionButtonClick(self):
        self.widgets['measurementFrame'].sourceWithCompliance()

    def maketipButtonClick(self):
        _t = 0
        _res = self.widgets['measurementFrame'].getResistanceReader()
        _meas = _res.read()
        try:
            ohms = float(_meas)
        except ValueError:
            ohms = 1000000.0
        if ohms > 200:  # 20Ω is compliance
            messagebox.showerror("Error", "No tip contact.")
            _res.kill()
            return
        self.widgets['stagecontroller'].raiseZaxis()
        time.sleep(0.1)
        while self.widgets['stagecontroller'].isbusy:
            try:
                ohms = float(_meas)
            except ValueError:
                ohms = 1000000.0
            logger.info(f"Measured {ohms:0.1f}Ω")
            if ohms > 100:
                logger.info("Resistance > 100Ω --> tip formed?")
                break
            _t += 1
            logger.debug(_t)
            if _t > 120:
                break
            time.sleep(0.1)
        self.widgets['stagecontroller'].stopZaxis()
        _res.kill()
        self.widgets['quitButton']['state'] = NORMAL
        messagebox.showinfo("Tip", "I think I made a tip..?")

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

    def checkJunctionsize(self, event):
        _junction_size = self.variables['junction_size'].get()
        _tip_size = self.variables['tip_size'].get()
        if not _junction_size or not _tip_size:
            return
        try:
            float(_junction_size)
            float(_tip_size)
        except ValueError:
            self.variables['junction_size'].set('1.0')
            self.variables['tip_size'].set('15')

    def checkOptions(self, *args):
        _outdir = Path(f"{self.variables['outputdirstring'].get()}")
        self.variables['outputdirstring'].set(str(_outdir))
        if self.variables['statusVar'].get() in (MEASURING):
            self.widgets['measButton'].after(100, self.checkOptions)
            return
        _initialized = [False, False, False]
        _connected = []
        if self.widgets['measurementFrame'].initialized:
            _connected.append('SMU')
            self.widgets['makejunctionButton']['state'] = NORMAL
            self.widgets['measButton']['state'] = NORMAL
            self.variables['statusVar'].set(" ".join(_connected)+" connected")
            _initialized[0] = True
        else:
            self.variables['statusVar'].set('Not Initialized')
        if self.widgets['stagecontroller'].initialized:
            _connected.append('Stage')
            _initialized[1] = True
        if self.widgets['tempcontrols'].initialized:
            _connected.append('Peltier')
            _initialized[2] = True
        if len(_connected) > 1:
            _connected = _connected[:-1]+['and', _connected[-1]]
        if not all(_initialized) and not self.variables['busy'].get():
            self.widgets['measButton'].after(100, self.checkOptions)
        if True in _initialized:
            self.initialized = True
        self.opts['isafm'] = self.variables['isafm'].get()
        parseusersettings(self.config_file, self.opts)

    def _checkafm(self, *args):
        _widget_map = {True: NORMAL, False: DISABLED}
        for widget in self.egain_widgets:
            self.widgets[widget]['state'] = _widget_map[self.isegain]
        for widget in self.afm_widgets:
            self.widgets[widget]['state'] = _widget_map[self.isafm]

    def _updateData(self, *args):
        if self.variables['sweepdone'].get():
            results = self.widgets['measurementFrame'].data
            if len(results['V']) == len(results['I']):
                self.widgets['dataplot'].displayData(results)
            self._writedata(False)
        if not self.widgets['measurementFrame'].isbusy:
            self._writedata(True)

    def _writedata(self, finalize=False):
        # TEMPERATURE DATA!!!
        # Save data to disk and then delete them
        # DATA_FORMAT = {'V':[], 'I':[], 't':[]}
        self.checkOptions()
        _jsize = float(self.variables['junction_size'].get())
        _rsize = float(self.variables['reference_size'].get()) / 2  # screen_cm in diameter / 2 = radius
        _tsize = float(self.variables['tip_size'].get()) / 2  # tip diameter / 2 = radius
        _conversion = (REFERENCE_SIZE_M * 100) / _rsize  # (m cm/m) / screen_cm = cm / screen_cm
        if self.isafm:  # calculate area from tip diameter
            logger.debug("Computing area from AFM tip diameter.")
            _area_in_cm = math.pi*(_tsize * 1e-07)**2
        else:
            logger.debug("Computing area from onscreen measurement.")
            _area_in_cm = math.pi*(_conversion * _jsize)**2  # pi((cm / screen_cm) screen_cm) = cm
        results = self.widgets['measurementFrame'].data
        for _key in ('J', 'upper', 'lower'):
            results[_key] = []
        for _I in results['I']:
            results['J'].append(_I/_area_in_cm)
            results['upper'].append(self.widgets['tempcontrols'].uppertemp)
            results['lower'].append(self.widgets['tempcontrols'].lowertemp)
        _fn = Path(self.opts['save_path'], self.opts['output_file_name'])
        _tmp = Path(f'{_fn}_tmp.txt')
        if finalize:
            logger.debug("Finalizing data.")
            data_f = Path(f'{_fn}_data.txt')
            if data_f.exists():
                if not messagebox.askyesno("Overwrite?", f'{data_f} exists, overwrite it?'):
                    _fn = increment_fn(_fn)
                    data_f = Path(f'{_fn}_data.txt')
            if write_data_to_file(data_f, results):
                _tmp.unlink(missing_ok=True)
            del self.widgets['measurementFrame'].data
        else:
            write_data_to_file(f'{_fn}_tmp.txt', results)

        with open(f'{_fn}_metadata.txt', 'w') as fh:
            fh.write(f'{time.strftime(STRFTIME)}\n')
            fh.write(f'Onscreen junction size:{_jsize}\n')
            fh.write(f"Magnification:{self.variables['junction_mag'].get()}\n")
            fh.write(f'Junction conversion factor:{_conversion}\n')
            fh.write(f"Thermopower measurement: {bool(self.widgets['measurementFrame'].measvolt.get())}\n")
            fh.write(f"Peltier enabled: {self.widgets['tempcontrols'].peltierstatus}\n")
            fh.write(f"Upper temperature (°C): {self.widgets['tempcontrols'].uppertemp}\n")
            fh.write(f"Lower temperature (°C): {self.widgets['tempcontrols'].lowertemp}\n")
        if finalize:
            messagebox.showinfo("Saved", f"Data written to {data_f}")
            self.opts['output_file_name'] = increment_fn(self.opts['output_file_name'])
            self.widgets['outputfilenameEntry'].delete(0, END)
            self.widgets['outputfilenameEntry'].insert(0, self.opts['output_file_name'])
            self.checkOptions()

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
        if self.widgets['measurementFrame'].isbusy or self.variables['busy'].get():
            self.widgets['quitButton']['state'] = DISABLED
            self.widgets['measButton']['state'] = DISABLED
        else:
            self.widgets['quitButton']['state'] = NORMAL
            self.widgets['measButton']['state'] = NORMAL
        if self.widgets['measurementFrame'].stopping:
            self.widgets['stopButton']['state'] = DISABLED
        else:
            self.widgets['stopButton']['state'] = NORMAL

    @property
    def isafm(self):
        return bool(self.variables['isafm'].get())

    @property
    def isegain(self):
        return not self.isafm

def increment_fn(fn):
    prts = str(fn).split('_')
    for _i in range(len(prts)-1, -1, -1):
        try:
            prts[_i] = str(int(prts[_i])+1).zfill(2)
            break
        except ValueError:
            continue
    new_fn = '_'.join(prts)
    if new_fn != fn:
        return new_fn
    elif fn[-4] == '.':
        return f'{fn[:-4]}_01{fn[-4:]}'
    else:
        return f'{fn}_01'

def write_data_to_file(fn, results):
    logger.debug("Writing to %s", fn)
    _fn = Path(fn)
    with _fn.open('w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='JV')
        writer.writerow(['V (V)', 'I (A)', 'J (A/cm2)', 'Time (s)', 'Upper Temp (°C)', 'Lower Temp (°C)'])
        for _idx, V in enumerate(results['V']):
            try:
                writer.writerow([V,
                                 results['I'][_idx],
                                 results['J'][_idx],
                                 results['t'][_idx],
                                 results['upper'][_idx],
                                 results['lower'][_idx]])
            except IndexError:
                logger.warning("Mismatch in lengths of data rows.")
    return _fn.exists()

def maketip(smu, stage):
    popup = Toplevel()
    popup.geometry('500x100+250-250')
    _msg = StringVar()
    Label(popup, textvariable=_msg).pack()