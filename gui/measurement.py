import os
import platform
import time
from decimal import Decimal
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, BooleanVar, IntVar, StringVar, Listbox, Label, Entry, messagebox
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from meas.k6430 import K6430
from meas.visa_subs import enumerateDevices
from meas.visa_subs import MODE_GPIB, MODE_SERIAL

# from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import


# def measureClick(sweep, meas):
#     smu = K6430(meas['GPIB'])
#     try:
#         smu.initialize()
#     except ValueError:

MEAS_MODE = MODE_SERIAL
# DATA_FORMAT = {'V':[], 'I':[], 'R':[], 't':[], 's':[]}
DATA_TEMPLATE = {'V':[], 'I':[], 't':[]}
DATA_FORMAT = ('V', 'I', 't')

class MeasurementControl(tk.Frame):

    error = False
    sweep = {'sweepLow': '-1.0',
             'sweepHigh': '1.0',
             'stepSize': '0.25',
             'nsweeps': '5',
             'reversed': '0'
             }

    meas = {'ADDRESS': '24',
            'NPLC': '5'
            }
    _isbusy = False
    mode = MEAS_MODE
    smu = None
    is_initialized = False
    child_threads = {'meas':[], 'read':[]}
    sweeps_done = 0
    results = {'V':[], 'I':[], 't':[]}

    def __init__(self, root, **kwargs):
        self.master = root
        self.measdone = kwargs.get('measdone', BooleanVar(value=False))
        self.busy = kwargs.get('busy', BooleanVar(value=False))
        self.measdone.set(False)
        super().__init__(self.master)
        self.labelFont = Font(size=8)
        self.deviceString = StringVar()
        self.createWidgets()

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
        self.results = {'V':[], 'I':[], 't':[]}

    @property
    def donemeasuring(self):
        return self.measdone.get()

    @property
    def isbusy(self):
        return self._isbusy

    def createWidgets(self):
        for _StringVar in self.sweep:
            setattr(self, _StringVar, StringVar(value=str(self.sweep[_StringVar])))
            getattr(self, _StringVar).trace_add('write', self.__validateSweep)
        sweepFrame = tk.LabelFrame(self, text='Sweep Settings')
        sweepLowEntry = tk.Entry(sweepFrame, textvariable=self.sweepLow, width=4)
        sweepHighEntry = tk.Entry(sweepFrame, textvariable=self.sweepHigh, width=4)
        sweepStepSizeEntry = tk.Entry(sweepFrame, textvariable=self.stepSize, width=4)
        sweepSweepsEntry = tk.Entry(sweepFrame, textvariable=self.nsweeps, width=4)

        sweepFrame.pack(side=LEFT, fill=BOTH)
        reversedCheckbutton = tk.Checkbutton(sweepFrame, text='Reversed',
                                             variable=self.reversed,
                                             command=self.__validateMeas)
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

        for _StringVar in self.meas:
            setattr(self, _StringVar, StringVar(value=str(self.meas[_StringVar])))
            getattr(self, _StringVar).trace_add('write', self.__validateMeas)
        measFrame = tk.LabelFrame(self, text='Sourcemeter Settings')

        measFrame.pack(side=LEFT, fill=BOTH)
        measNPLC = tk.Spinbox(measFrame,
                              from_=1,
                              to=10,
                              increment=1,
                              textvariable=self.NPLC,
                              width=4)
        devicePicker = tk.OptionMenu(measFrame,
                                     self.deviceString,
                                     'Choose SMU device',
                                     *enumerateDevices())
        self.deviceString.trace('w', self.__initdevice)
        measNPLCLabel = tk.Label(measFrame, text='NPLC:', font=self.labelFont)
        measNPLCLabel.pack(side=LEFT)
        measNPLC.pack(side=LEFT)
        measdevicePickerLabel = tk.Label(measFrame, text='Adress:', font=self.labelFont)
        measdevicePickerLabel.pack(side=LEFT)
        devicePicker.pack(side=LEFT)

    def shutdown(self):
        if self.smu is not None:
            self.smu.close()

    def __initdevice(self, *args):
        self.busy.set(True)
        self._isbusy = True
        if not self.is_initialized:
            _smu = K6430(self.deviceString.get())
            if _smu.initialize(auto_sense_range=True):
                self.smu = _smu
        if self.smu is not None:
            self.is_initialized = True
        self.busy.set(False)
        self._isbusy = False

    def __validateSweep(self, *args):
        try:
            for _StringVar in self.sweep:
                _var = getattr(self, _StringVar).get()
                if _var:
                    float(_var)
                    self.sweep[_StringVar] = _var
                # if _StringVar in ('nsweeps', 'reversed'):
                #    self.sweep[_StringVar] = int(getattr(self, _StringVar).get())
                # else:
                #    self.sweep[_StringVar] = float(getattr(self, _StringVar).get())
        except ValueError as msg:
            getattr(self, _StringVar).set(self.sweep[_StringVar])
            print(f'{_StringVar} invalid.')
            print(msg)
            self.error = True
            return
        self.error = False

    def __validateMeas(self, *args):
        try:
            for _StringVar in self.meas:
                _var = getattr(self, _StringVar).get()
                int(_var)
                self.meas[_StringVar] = _var
                # self.meas[_StringVar] = int(getattr(self, _StringVar).get())
        except ValueError as msg:
            print(f'{_StringVar} invalid {str(msg)}.')
            getattr(self, _StringVar).set(self.meas[_StringVar])
            self.error = True
            return
        self.error = False

    def stop_measurement(self):
        for _key in self.child_threads:
            for child in self.child_threads[_key]:
                child[0].clear()
                while child[1].is_alive():
                    time.sleep(0.1)
        self.smu.end_voltage_sweep()
        self._measureinbackground()

    def startMeasurementButtonClick(self):
        if self.error:
            messagebox.showerror("Error", "Invalid settings.")
            return
        if self.smu is None:
            messagebox.showerror("Error", "SMU config error.")
            return
        if not self.is_initialized:
            messagebox.showerror("Error", "SMU not initialized.")
            return
        # self.measdone.set(False)
        self.busy.set(True)
        self._isbusy = True
        self.smu.initialize(auto_sense_range=True)
        self.smu.setNPLC(self.meas['NPLC'])
        self.child_threads['meas'].append(self.smu.start_voltage_sweep(build_sweep(self.sweep)))
        self.child_threads['meas'][-1][1].start()
        self._measureinbackground()

    def getResistanceReader(self):
        if not self.is_initialized:
            messagebox.showerror("Error", "Sourcemeter is not initialized.")
            return
        self.child_threads['read'].append(self.smu.measure_resistance())
        self.child_threads['read'][-1][1].start()
        self.after(500, self._readinbackground)
        return self.child_threads['read'][-1]

    def _readinbackground(self):
        self.busy.set(True)
        self._isbusy = True
        if self.child_threads['read']:
            if self.child_threads['read'][-1][1].active:
                # print(self.child_threads['read'][-1][0].is_set())
                self.after(100, self._readinbackground)
                return
            else:
                self.child_threads['read'].pop()
        self.smu.disarm()
        self.busy.set(False)
        self._isbusy = False

    def _measureinbackground(self):
        if not self.is_initialized:
            return
        self.measdone.set(False)
        self.busy.set(True)
        self._isbusy = True
        if self.child_threads['meas']:
            if not self.child_threads['meas'][-1][1].active:
                self._process_data(self.smu.fetch_data().split(','))
                self.child_threads['meas'].pop()
                self.sweeps_done += 1
                if self.sweeps_done < int(self.sweep["nsweeps"]):
                    self.child_threads['meas'].append(self.smu.start_voltage_sweep(build_sweep(self.sweep)))
                    self.measdone.set(True)
                    self.child_threads['meas'][-1][1].start()
                else:
                    print(f'Completed {self.sweep["nsweeps"]} sweeps.')
                    self.sweeps_done = 0
            self.after(100, self._measureinbackground)
            return
        print('All sweeps completed.')
        self.smu.end_voltage_sweep()
        self.measdone.set(True)
        self.busy.set(False)
        self._isbusy = False

    def _process_data(self, data_):
        # b'VOLT,CURR,TIME ---> self.visa.write(":FORM:ELEM VOLT,CURR,TIME") 
        # _data = DATA_FORMAT
        _keymap = {}
        for i, j in enumerate(DATA_FORMAT):
            _keymap[i] = j
        print(_keymap)
        i = 0
        for _d in data_:
            if i == len(_keymap):
                i = 0
            print(f'{i}:{_keymap[i]} = {_d}')
            try:
                self.results[_keymap[i]].append(float(_d))
            except ValueError:
                self.results[_keymap[i]].append(0.0)
            i += 1
        # print(self.results)

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
