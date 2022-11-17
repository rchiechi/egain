import os
import platform
import logging
import threading
from decimal import Decimal
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, Listbox, Label, Entry, messagebox
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
    mode = MEAS_MODE
    smu = None
    is_initialized = False

    def __init__(self, root, **kwargs):
        self.master = root
        self.measdone = kwargs['measdone']
        self.busy = kwargs['busy']
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
        sweepLowEntryLabel = tk.Label(sweepFrame, text='From:', font=self.labelFont)
        sweepLowEntryLabel.pack(side=LEFT)
        sweepLowEntry.pack(side=LEFT)
        sweepHighEntryLabel = tk.Label(sweepFrame, text='To:', font=self.labelFont)
        sweepHighEntryLabel.pack(side=LEFT)
        reversedCheckbutton = tk.Checkbutton(sweepFrame, text='Reversed',
                                             variable=self.reversed,
                                             command=self.__validateMeas)
        reversedCheckbutton.pack(side=LEFT)
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

    def __initdevice(self, *args):
        if not self.is_initialized:
            self.smu = K6430(self.deviceString.get())
        if self.smu is not None:
            self.is_initialized = True

    def __validateSweep(self, *args):
        try:
            for _StringVar in self.sweep:
                _var = getattr(self, _StringVar).get()
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
        print(build_sweep(self.sweep))

    def startMeasurementButtonClick(self):
        if self.error:
            messagebox.showerror("Error", "Invalid settings, cannot start sweep.")
            return
        if self.smu is None:
            messagebox.showerror("Error", "Sourcemeter is not configured correctly.")
            return

    def _measureinbackground(self):
        self.measdone.set(False)
        self.busy.set(True)
        self.smu.initialize()
        self.measdone.set(True)
        self.busy.set(False)


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
        return list(map(float, _sweepdown+_sweepup+[_zero]))
    return list(map(float, _sweepup+_sweepdown+[_zero]))


class MeasureThread(threading.Thread):

    def __init__(self, smu, sweep):
        super().__init__()
        self.smu = smu
        self.sweep = sweep

    def run(self):
       # _sweep = 
        self.smu.voltage_sweep()



if __name__ == '__main__':
    root = Tk()
    main = MeasurementControl(root)
    main.pack()
    root.mainloop()
