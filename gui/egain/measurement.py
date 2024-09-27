import logging
from decimal import Decimal
import tkinter.ttk as tk
from tkinter import Tk
from tkinter import BooleanVar, StringVar, messagebox
from tkinter import TOP, LEFT, RIGHT, BOTTOM
from tkinter import BOTH
from tkinter.font import Font
from tkinter import DISABLED, NORMAL
from meas.k6430 import K6430
from meas.k2182A import K2182A
from meas.util import enumerateDevices
from meas.visa_subs import MODE_SERIAL
from gui.util import parseusersettings

MEAS_MODE = MODE_SERIAL

logger = logging.getLogger(__package__+'.meas')

class MeasurementControl(tk.Frame):

    error = False
    _isbusy = False
    mode = MEAS_MODE
    smu = None
    is_initialized = False
    child_threads = {'meas': None, 'read': None}
    sweeps_done = 0
    config_file = 'MeasurementControl.json'

    SWEEP_PROTO = {'sweepLow': '-1.0',
                   'sweepHigh': '1.0',
                   'stepSize': '0.25',
                   'nsweeps': '5',
                   'reversed': '0',
                   'measvolt': '0'
                   }
    MEAS_PROTO = {'ADDRESS': '24', 'NPLC': '5', 'compliance': '105e-3'}

    def __init__(self, root, cli_opts, **kwargs):
        self.master = root
        self._init_results()
        self.cli_opts = cli_opts
        self.sweepdone = kwargs.get('sweepdone', BooleanVar(value=False))
        self.busy = kwargs.get('busy', BooleanVar(value=False))
        self.sweepdone.set(False)
        super().__init__(self.master)
        self.labelFont = Font(size=8)
        self.config = parseusersettings(self.config_file)
        self.sweep = self.config.get('sweep', self.SWEEP_PROTO)
        self.meas = self.config.get('meas', self.MEAS_PROTO)
        self.deviceString = StringVar()
        self.stop = False
        self.sweepcompletesound = StringVar()
        self.widgets = {}
        self.createWidgets()

    def _init_results(self):
        self.results = {}
        for key in K6430.DATA_FORMAT:
            self.results[key] = []

    @property
    def initialized(self):
        if not self.error and self.is_initialized:
            return True
        return False

    @property
    def voltage_sweep(self):
        return build_sweep(self.sweep)

    @property
    def sweepparams(self):
        return self.sweep

    @property
    def data(self):
        return self.results

    @data.deleter
    def data(self):
        self._init_results()

    @property
    def donemeasuring(self):
        return self.sweepdone.get()

    @property
    def isbusy(self):
        return self._isbusy

    @isbusy.setter
    def isbusy(self, status):
        if status:
            self.busy.set(True)
            self._isbusy = True
        else:
            self.busy.set(False)
            self._isbusy = False

    @property
    def stopping(self):
        if self.isbusy and self.stop:
            return True
        return False

    def createWidgets(self):
        for _StringVar in self.SWEEP_PROTO:
            _val = self.sweep.get(_StringVar, self.SWEEP_PROTO[_StringVar])
            setattr(self, _StringVar, StringVar(value=_val))
            getattr(self, _StringVar).trace_add('write', self._validateSweep)
        sweepFrame = tk.LabelFrame(self, text='Sweep Settings')
        sweepLowEntry = tk.Entry(sweepFrame, textvariable=self.sweepLow, width=4)
        self.widgets['sweepLowEntry'] = sweepLowEntry
        sweepHighEntry = tk.Entry(sweepFrame, textvariable=self.sweepHigh, width=4)
        self.widgets['sweepHighEntry'] = sweepHighEntry
        sweepStepSizeEntry = tk.Entry(sweepFrame, textvariable=self.stepSize, width=4)
        self.widgets['sweepStepSizeEntry'] = sweepStepSizeEntry
        # sweepSweepsEntry = tk.Entry(sweepFrame, textvariable=self.nsweeps, width=4)
        sweepSweepsEntry = tk.Spinbox(sweepFrame,
                                      font=Font(size=10),
                                      from_=1,
                                      to=20,
                                      increment=1,
                                      textvariable=self.nsweeps,
                                      width=4)
        self.widgets['sweepSweepsEntry'] = sweepSweepsEntry
        sweepFrame.pack(side=BOTTOM, fill=BOTH)
        reversedCheckbutton = tk.Checkbutton(sweepFrame, text='Reversed',
                                             variable=self.reversed,
                                             command=self._validateMeas)
        self.widgets['reversedCheckbutton'] = reversedCheckbutton
        reversedCheckbutton.pack(side=LEFT)
        sweepLowEntryLabel = tk.Label(sweepFrame, text='From:', font=self.labelFont)
        sweepLowEntryLabel.pack(side=LEFT)
        sweepLowEntry.pack(side=LEFT)
        sweepHighEntryLabel = tk.Label(sweepFrame, text='To:', font=self.labelFont)
        sweepHighEntryLabel.pack(side=LEFT)
        sweepHighEntry.pack(side=LEFT)
        sweepHighEntryLabel = tk.Label(sweepFrame, text='Step Size:', font=self.labelFont)
        sweepHighEntryLabel.pack(side=LEFT)
        sweepStepSizeEntry.pack(side=LEFT)
        sweepSweepsLabel = tk.Label(sweepFrame, text='Sweeps:', font=self.labelFont)
        sweepSweepsLabel.pack(side=LEFT)
        sweepSweepsEntry.pack(side=LEFT)
        measvoltCheckbutton = tk.Checkbutton(sweepFrame, text='Seebeck',
                                             variable=self.measvolt,
                                             command=self._validateMeas)
        measvoltCheckbutton.pack(side=RIGHT)

        for _StringVar in self.meas:
            setattr(self, _StringVar, StringVar(value=str(self.meas[_StringVar])))
            getattr(self, _StringVar).trace_add('write', self._validateMeas)
        measFrame = tk.LabelFrame(self, text='Sourcemeter Settings')

        measFrame.pack(side=BOTTOM, fill=BOTH)

        measComplianceEntry = tk.Entry(measFrame, textvariable=self.compliance, width=10)
        measComplianceLabel = tk.Label(measFrame, text='Compliance:', font=self.labelFont)
        measCompleteSoundCheckBox = tk.Checkbutton(measFrame,
                                                   text='Completion Sound',
                                                   variable=self.sweepcompletesound)
        measComplianceLabel.pack(side=LEFT)
        measComplianceEntry.pack(side=LEFT)
        measCompleteSoundCheckBox.pack(side=RIGHT)

        measNPLC = tk.Spinbox(measFrame,
                              from_=1,
                              to=10,
                              increment=1,
                              textvariable=self.NPLC,
                              width=4)
        devicePicker = tk.OptionMenu(measFrame,
                                     self.deviceString,
                                     'Choose SMU device',
                                     *enumerateDevices(first='ttyUSB0'))
        self.deviceString.trace('w', self._initdevice)
        measNPLCLabel = tk.Label(measFrame, text='NPLC:', font=self.labelFont)
        measNPLCLabel.pack(side=LEFT)
        measNPLC.pack(side=LEFT)
        measdevicePickerLabel = tk.Label(measFrame, text='Adress:', font=self.labelFont)
        measdevicePickerLabel.pack(side=LEFT)
        devicePicker.pack(side=LEFT)
        if 'device_string' in self.config:
            self.deviceString.set(self.config['device_string'])
            self._initdevice()

    def shutdown(self):
        if self.smu is not None:
            self.smu.close()

    def _saveconfig(self):
        parseusersettings(self.config_file, self.config)

    def _initdevice(self, *args):
        self.isbusy = True
        if not self.is_initialized:
            _smu = K6430(self.deviceString.get(), quiet=self.cli_opts.quiet)
            if _smu.initialize(auto_sense_range=True,
                               flowcontrol=True,
                               compliance=float(self.compliance.get())):
                self.smu = _smu
                self.config['device_string'] = self.deviceString.get()
                self._saveconfig()
        if self.smu is not None:
            self.is_initialized = True
        self.isbusy = False

    def _validateSweep(self, *args):
        try:
            for _StringVar in self.SWEEP_PROTO:
                _var = getattr(self, _StringVar).get()
                if _var:
                    float(_var)
                    self.sweep[_StringVar] = _var
        except ValueError as msg:
            getattr(self, _StringVar).set(self.sweep[_StringVar])
            logger.debug(f'{_StringVar} invalid ({msg}).')
            self.error = True
            return
        self.error = False
        self.config['sweep'] = self.sweep
        self._saveconfig()

    def _validateMeas(self, *args):
        self._seebeckMode(int(self.measvolt.get()))
        try:
            for _StringVar in self.MEAS_PROTO:
                _var = getattr(self, _StringVar).get()
                try:
                    int(_var)
                except ValueError:
                    float(_var)
                self.meas[_StringVar] = _var
        except ValueError as msg:
            logger.warning(f'{_StringVar} invalid {str(msg)}.')
            getattr(self, _StringVar).set(self.meas[_StringVar])
            self.error = True
            return
        self.error = False
        self.config['meas'] = self.meas
        self._saveconfig()

    def _seebeckMode(self, set_on):
        _state = NORMAL
        if set_on:
            _state = DISABLED
        for _widget in ('sweepLowEntry',
                        'sweepHighEntry',
                        'sweepStepSizeEntry',
                        'reversedCheckbutton'):
            self.widgets[_widget]['state'] = _state

    def stop_measurement(self):
        self.stop = True

    def startMeasurementButtonClick(self):
        self.stop = False
        if self.error:
            messagebox.showerror("Error", "Invalid settings.")
            return
        if self.smu is None:
            messagebox.showerror("Error", "SMU config error.")
            return
        if not self.is_initialized:
            messagebox.showerror("Error", "SMU not initialized.")
            return
        self.isbusy = True
        self.smu.initialize(reset=True,
                            auto_sense_range=True,
                            flowcontrol=False,
                            compliance=float(self.compliance.get()))
        self.sweeps_done = 0
        if int(self.measvolt.get()):
            self.child_threads['meas'] = self.smu.measure_voltage(compliance=self.meas['compliance'],
                                                                  NPLC=self.meas['NPLC'])
            self.child_threads['meas'].start()
            self._measureVoltageinbackground()
        else:
            self.child_threads['meas'] = self.smu.start_voltage_sweep(build_sweep(self.sweep),
                                                                      compliance=self.meas['compliance'],
                                                                      NPLC=self.meas['NPLC'])
            self.child_threads['meas'].start()
            self._measureinbackground()

    def getResistanceReader(self):
        if not self.is_initialized:
            messagebox.showerror("Error", "Sourcemeter is not initialized.")
            return
        self.child_threads['read'] = self.smu.measure_resistance()
        self.child_threads['read'].start()
        self.after(500, self._readinbackground)
        return self.child_threads['read']

    def sourceWithCompliance(self, **kwargs):
        volts = kwargs.get('voltage', 0.1)
        compliance = kwargs.get('compliance', 1e-6)
        self.smu.source_with_compliance(volts, compliance)

    def _measureVoltageinbackground(self, **kwargs):
        if not self.is_initialized:
            messagebox.showerror("Error", "Sourcemeter is not initialized.")
            return
        self.isbusy = True
        self.sweepdone.set(False)
        if self.child_threads['meas'] is not None:
            if self.child_threads['meas'].active:
                if not self.stop:
                    self._process_data(self.child_threads['meas'].read().split(b','))
                self.sweeps_done += 1
                if self.sweeps_done >= int(self.sweep["nsweeps"]) and not self.stop:
                    logger.debug('Completed voltage measurement.')
                    self.child_threads['meas'].kill()
                    self.child_threads['meas'] = None
                    self.sweeps_done = 0
            elif self.stop and not self.child_threads['meas'].aborted:
                self.child_threads['meas'].abort()
                self.sweepdone.set(True)
            self.after(100, self._measureVoltageinbackground)
            return
        self.smu.end_voltage_sweep(self.sweepcompletesound.get() == '1')
        self.isbusy = False
        self.sweepdone.set(True)
        self.smu.disarm()
        logger.info('Voltage measurement completed.')

    def _readinbackground(self):
        self.isbusy = True
        if self.child_threads['read'] is not None:
            if self.child_threads['read'].active:
                self.after(100, self._readinbackground)
                return
            else:
                self.child_threads['read'] = None
        self.smu.disarm()
        self.isbusy = False

    def _measureinbackground(self):
        if not self.is_initialized:
            messagebox.showerror("Error", "Sourcemeter is not initialized.")
            return
        self.isbusy = True
        self.sweepdone.set(False)
        if self.child_threads['meas'] is not None:
            if not self.child_threads['meas'].active:
                if not self.stop:
                    self._process_data(self.smu.fetch_data().split(','))
                self.sweeps_done += 1
                if self.sweeps_done < int(self.sweep["nsweeps"]) and not self.stop:
                    logger.debug('Finishing sweep and starting next.')
                    self.child_threads['meas'] = self.smu.start_voltage_sweep(build_sweep(self.sweep))
                    self.child_threads['meas'].start()
                else:
                    logger.info(f'Completed {self.sweep["nsweeps"]} sweeps.')
                    self.child_threads['meas'] = None
                    self.sweeps_done = 0
            elif self.stop and not self.child_threads['meas'].aborted:
                self.child_threads['meas'].abort()
                self.sweepdone.set(True)
            self.after(100, self._measureinbackground)
            return
        self.smu.end_voltage_sweep(self.sweepcompletesound.get() == '1')
        self.isbusy = False
        self.sweepdone.set(True)
        self.smu.disarm()
        logger.info('All sweeps completed.')

    def _process_data(self, data_):
        # b'VOLT,CURR,TIME ---> self.visa.write(":FORM:ELEM VOLT,CURR,TIME")
        # _data = DATA_FORMAT
        _keymap = {}
        for i, j in enumerate(K6430.DATA_FORMAT):
            _keymap[i] = j
        logger.debug(_keymap)
        i = 0
        for _d in data_:
            if i == len(_keymap):
                i = 0
            logger.debug(f'{i}:{_keymap[i]} = {_d}')
            try:
                self.results[_keymap[i]].append(float(_d))
            except ValueError:
                logger.warning(f'Error convering {_d} to float.')
                self.results[_keymap[i]].append(0.0)
            i += 1
        self.sweepdone.set(True)

class MeasurementReadV(MeasurementControl):

    measvoltage = 0.0

    def createWidgets(self):
        self.voltageString = StringVar(value=f'{self.voltage} V')
        nplcFrame = tk.Frame(self)
        measFrame = tk.Frame(self)
        for _StringVar in self.meas:
            setattr(self, _StringVar, StringVar(value=str(self.meas[_StringVar])))
            getattr(self, _StringVar).trace_add('write', self._validateMeas)
        measNPLC = tk.Spinbox(nplcFrame,
                              from_=1,
                              to=10,
                              increment=1,
                              textvariable=self.NPLC,
                              width=4)
        devicePicker = tk.OptionMenu(nplcFrame,
                                     self.deviceString,
                                     'Choose Voltmeter',
                                     *enumerateDevices(first='ttyUSB0'))
        self.deviceString.trace('w', self._initdevice)
        measNPLCLabel = tk.Label(nplcFrame, text='NPLC:', font=self.labelFont)
        measNPLCLabel.pack(side=LEFT)
        measNPLC.pack(side=LEFT)
        measdevicePickerLabel = tk.Label(nplcFrame, text='Adress:', font=self.labelFont)
        measdevicePickerLabel.pack(side=LEFT)
        devicePicker.pack(side=LEFT)
        nplcFrame.pack(side=TOP)
        measFrame.pack(side=TOP, fill=BOTH)

        readoutLabel = tk.Label(measFrame, text='Voltage:')
        voltageLabel = tk.Label(measFrame, textvariable=self.voltageString)
        self.after(100, self._readvoltage)
        readoutLabel.pack(side=LEFT)
        voltageLabel.pack(side=LEFT)

    def _updateVoltage(self):
        self.voltageString.set(f'{self.voltage} V')

    def _init_results(self):
        self.results = {}
        for key in K2182A.DATA_FORMAT:
            self.results[key] = []

    def _initdevice(self, *args):
        self.isbusy = True
        if not self.is_initialized:
            _smu = K2182A(self.deviceString.get())
            if _smu.initialize(auto_sense_range=True):
                self.smu = _smu
        if self.smu is not None:
            self.is_initialized = True
        self.isbusy = False

    def _readvoltage(self):
        self.after(500, self._readvoltage)
        if not self.initialized:
            return
        _voltage = self.smu.fetch_data()
        try:
            self.measvoltage = float(_voltage)
        except ValueError:
            logger.warning(f"Error converting {_voltage} to float.")
            self.measvoltage = 0.0
        self._updateVoltage()

    @property
    def voltage(self):
        return self.measvoltage

def build_sweep(sweep):
    _sweepup = []
    _sweepdown = []
    _zero = Decimal('0.0')
    _v = _zero
    while _v <= Decimal(sweep['sweepHigh']):
        _sweepup.append(_v)
        _v += Decimal(sweep['stepSize'])
    _sweepup += list(reversed(_sweepup))[1:-1]
    _v = _zero
    while _v >= Decimal(sweep['sweepLow']):
        _sweepdown.append(_v)
        _v -= Decimal(sweep['stepSize'])
    _sweepdown += list(reversed(_sweepdown))[1:-1]

    if sweep['reversed']:
        return list(map(str, _sweepup+_sweepdown+[_zero]))
    return list(map(str, _sweepdown+_sweepup+[_zero]))


if __name__ == '__main__':
    root = Tk()
    main = MeasurementControl(root)
    main.pack()
    root.mainloop()
