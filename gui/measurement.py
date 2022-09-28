import os
import platform
import logging
import threading
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
# from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import


# def measureClick(sweep, meas):
#     smu = K6430(meas['GPIB'])
#     try:
#         smu.initialize()
#     except ValueError:
        
class MeasurementControl(tk.Frame):

    error = False
    sweep = {'sweepLow': -1.0,
             'sweepHigh': 1.0,
             'stepSize': 0.25,
             'Sweeps': 5,
             }

    meas = {'GPIB': 24,
            'NPLC': 25
            }

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self.labelFont = Font(size=8)
        self.device = StringVar()
        self.createWidgets()

    def createWidgets(self):
        for _StringVar in self.sweep:
            setattr(self, _StringVar, StringVar(value=str(self.sweep[_StringVar])))
            getattr(self, _StringVar).trace_add('write', self.__validateSweep)
        sweepFrame = tk.LabelFrame(self, text='Sweep Settings')
        sweepLowEntry = tk.Entry(sweepFrame, textvariable=self.sweepLow, width=4)
        sweepHighEntry = tk.Entry(sweepFrame, textvariable=self.sweepHigh, width=4)
        sweepStepSizeEntry = tk.Entry(sweepFrame, textvariable=self.stepSize, width=4)
        sweepSweepsEntry = tk.Entry(sweepFrame, textvariable=self.Sweeps, width=4)

        sweepFrame.pack(side=LEFT, fill=BOTH)
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
        measNPLC = tk.Entry(measFrame, textvariable=self.NPLC, width=4)
        devicePicker = tk.OptionMenu(measFrame,
                                     self.device,
                                     'Choose VISA device',
                                     *enumerateDevices())
        measNPLCLabel = tk.Label(measFrame, text='NPLC:', font=self.labelFont)
        measNPLCLabel.pack(side=LEFT)
        measNPLC.pack(side=LEFT)
        measdevicePickerLabel = tk.Label(measFrame, text='GPIB:', font=self.labelFont)
        measdevicePickerLabel.pack(side=LEFT)
        devicePicker.pack(side=LEFT)


        # measurementButton = tk.Button(self, text='Measure')

    def __validateSweep(self, *args):
        try:
            for _StringVar in self.sweep:
                self.sweep[_StringVar] = float(getattr(self, _StringVar).get())
        except ValueError:
            # print(f'{getattr(self, _StringVar).get()} is invalid input.')
            self.error = True
            # self.sweep[_StringVar] = getattr(self, _StringVar).set(self.sweep[_StringVar])
            return
        self.error = False

    def __validateMeas(self, *args):
        try:
            for _StringVar in self.meas:
                self.meas[_StringVar] = int(getattr(self, _StringVar).get())
        except ValueError:
            # print(f'{getattr(self, _StringVar).get()} is invalid input.')
            self.error = True
            # self.sweep[_StringVar] = getattr(self, _StringVar).set(self.sweep[_StringVar])
            return
        self.error = False

    def startMeasurementButtonClick(self):
        if self.error:
            messagebox.showerror("Error", "Invalid settings, cannot start sweep.")
            return
        smu = K6430(self.meas['GPIB'])
        try:
            smu.initialize()
        except AttributeError:
            messagebox.showerror("Error", "Sourcemeter is not configured correctly.")
            return



if __name__ == '__main__':
    root = Tk()
    main = MeasurementControl(root)
    main.pack()
    root.mainloop()
