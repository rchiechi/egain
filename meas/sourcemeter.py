"""
forked from https://github.com/HuangJunye/GrapheneLab-Measurement-Code.git
"""
import time
import numpy as np
import meas.visa_subs as visa_subs
from meas.visa_subs import MODE_GPIB, MODE_SERIAL
from meas.notes import Music
# import serial

VOLT = 'VOLT'
CURR = 'CURR'
DEFAULTMODE = VOLT


class Instrument:
    """Implement a generic instrument which does the following:

    description
    """

    visa = None

    def __init__(self, address):
        self.name = "Instrument Name"
        self.address = address
        if isinstance(address, int):
            self.visa = visa_subs.initialize_gpib(address, 0)
            self.backend = MODE_GPIB
        else:
            # self.visa = serial.Serial(address, 9600, timeout=0.5)
            self.visa = visa_subs.initialize_serial(address)
            self.backend = MODE_SERIAL

    @property
    def initialized(self):
        if self.visa is not None:
            return True
        return False

    def description(self):
        """ Print a description string to data file"""

        return f"{self.name}: address={self.address}"


class Keithley(Instrument):
    """Implement a generic keitheley sourcemeter for k6430, k2400 and k2002
    Based on generic Instrument class, add the following methods:

    initialize
    ramp

    """

    mode = DEFAULTMODE
    data = [0.0, 0.0]
    source_column = 0
    data_column = 1
    source = ""
    sense = ""
    ramp_step = 0
    source_range = 0
    sense_range = 0
    auto_range = True
    output = False

    def description(self):
        """ Print a description string to data file"""

        description_string = (
            f"{super().description()}, "
            f"source={self.source}, "
            f"sense={self.sense} "
            "\n"
        )
        return description_string

    def initialize(self, **kwargs):
        """Initialize Keithley sourcemeter with specified mode, and other parameters.
           Defaults:
                 mode=VOLT, source_range=21, sense_range=105e-9, compliance=105e-9,
                 ramp_step=0.1, auto_sense_range=False, reset=True
        """

        if self.visa is None:
            return False

        if self.mode == VOLT:
            self.source = VOLT
            self.sense = CURR
            self.source_column = 0
            self.data_column = 1
        elif self.mode == CURR:
            self.source = CURR
            self.sense = VOLT
            self.source_column = 1
            self.data_column = 0
        else:
            raise ValueError(f"This mode does exist! Please input {VOLT} or {CURR} only.")

        self.column_names = "V (V),I (A)"
        self.source_range = kwargs.get('source_range', 21)
        self.sense_range = kwargs.get('sense_range', 105e-9)
        self.ramp_step = kwargs.get('ramp_step', 0.1)
        self.data = [0.0, 0.0]

        if kwargs.get('reset', True):
            self.output = False
            self.visa.write(":OUTP OFF")
            self.visa.write("*RST")
            # self.visa.write(":SYST:BEEP:STAT OFF")

            self.visa.write(f":SOUR:FUNC:MODE {self.source}")
            # self.visa.write(f":SOUR:{self.source}:RANG {self.source_range:.2e}")
            if kwargs.get('auto_sense_range', False):
                self.visa.write(f":SENS:{self.sense}:RANG:AUTO ON")
            else:
                self.auto_range = True
                self.visa.write(f":SENS:{self.sense}:RANG {self.sense_range:.2e}")

            compliance = kwargs.get('compliance', 105e-9)
            self.visa.write(f":SENS:{self.sense}:PROT:LEV {compliance:.3e}")

            # Configure the auto zero (reference)
            self.visa.write(":SYST:AZER:STAT ON")
            self.visa.write(":SYST:AZER:CACH:STAT ON")
            self.visa.write(":SYST:AZER:CACH:RES")

            # Disable concurrent mode, measure I and V (not R)
            self.visa.write(":SENS:FUNC:CONC OFF")
            # self.visa.write(":SENS:FUNC:ON 'VOLT','CURR'")
            self.visa.write(":FORM:ELEM VOLT,CURR")

        else:
            self.__checkarmed()
            compliance = float(self.visa.query(":SENS:CURR:PROT:LEV?"))
            self.read_data()
        return True

    def setNPLC(self, nplc):
        self.visa.write(f':SENSE:{self.sense}:NPLC {nplc}')

    def start_voltage_sweep(self, v_list):
        # self.visa.write('*RST')
        # print(self.visa.query(':OUTP:STAT?'))
        self.visa.write(':SYST:TIME:RES')
        self.visa.write(':SOUR:FUNC:MODE VOLT')
        self.visa.write(":SENS:FUNC 'CURR:DC'")
        if self.auto_range:
            self.visa.write(":SENS:CURR:RANG:AUTO ON")
        else:
            self.visa.write(f":SENS:CURR:RANG {self.sense_range:.2e}")
        self.visa.write(':SOUR:DEL:AUTO ON')
        self.visa.write(f':SOUR:LIST:VOLT {",".join(v_list)}')
        _points = self.visa.query(':SOUR:LIST:VOLT:POIN?')
        if not _points:
            _points = len(v_list)
        self.visa.write(f':TRIG:COUN {_points}')
        self.visa.write(':SOUR:VOLT:MODE LIST')
        self.arm()
        self.visa.write(':INIT')
        return self.visa.get_wait_for_meas()

    def measure_resistance(self, _range='20'):
        self.visa.write(':SYST:TIME:RES')
        self.visa.write(":SENS:FUNC 'RES'")
        self.visa.write(f':SENS:RES:RANG {_range}')
        self.visa.write(':SENS:RES:MODE AUTO')
        self.arm()
        return self.visa.get_reader()

    def end_voltage_sweep(self):
        self.disarm()

    def arm(self):
        self.visa.write(':OUTP ON')
        self.__checkarmed()

    def disarm(self):
        self.visa.write(':OUTP OFF')
        self.__checkarmed()

    def __checkarmed(self):
        self.output = bool(int(self.visa.query(":OUTP:STAT?")))

    def fetch_data(self):
        return self.visa.query('FETC?')

    def close(self):
        if self.visa is not None:
            self.visa.close()

    @property
    def armed(self):
        return self.output

