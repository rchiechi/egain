"""
forked from https://github.com/HuangJunye/GrapheneLab-Measurement-Code.git
"""

import time
import meas.visa_subs as visa_subs
from meas.visa_subs import MODE_GPIB, MODE_SERIAL
# from meas.notes import Music

VOLT = 'VOLT'
CURR = 'CURR'
TEMP = 'TEMP'
DEFAULTMODE = VOLT

class Instrument:
    """Implement a generic instrument which does the following:

    description
    """
    DATA_FORMAT = ('V', 'I', 't')
    visa = None

    def __init__(self, address, **kwargs):
        self.name = "Instrument Name"
        self.address = address
        if isinstance(address, int):
            self.visa = visa_subs.initialize_gpib(address, 0)
            self.backend = MODE_GPIB
        else:
            # self.visa = serial.Serial(address, 9600, timeout=0.5)
            self.visa = visa_subs.initialize_serial(address,
                                                    flowcontrol=kwargs.get('flowcontrol', False),
                                                    quiet=kwargs.get('quiet', False))
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
            if kwargs.get('auto_sense_range', True):
                self.auto_range = True
                self.visa.write(f":SENS:{self.sense}:RANG:AUTO ON")
            else:
                self.visa.write(f":SENS:{self.sense}:RANG {self.sense_range:.2e}")

            # compliance = kwargs.get('compliance', 105e-3)
            # self.visa.write(f":SENS:{self.sense}:PROT:LEV {compliance:.3e}")
            self.set_compliance(kwargs.get('compliance', 105e-3))

            # Configure the auto zero (reference)
            self.visa.write(":SYST:AZER:STAT ON")
            self.visa.write(":SYST:AZER:CACH:STAT ON")
            self.visa.write(":SYST:AZER:CACH:RES")

            # Disable concurrent mode, measure I and V (not R)
            self.visa.write(":SENS:FUNC:CONC OFF")
            # self.visa.write(":SENS:FUNC:ON 'VOLT','CURR'")
            self.visa.write(":FORM:ELEM VOLT,CURR,TIME")

        else:
            self.__checkarmed()
            # compliance = float(self.visa.query(":SENS:CURR:PROT:LEV?"))
            self.read_data()
        self.disarm()
        return True

    def set_compliance(self, compliance):
        self.visa.write(f":SENS:{self.sense}:PROT:LEV {compliance:.3e}")

    def setNPLC(self, nplc):
        self.visa.write(f':SENSE:{self.sense}:NPLC {nplc}')

    def clearbuffer(self):
        self.visa.write(':TRAC:CLE')

    def start_voltage_sweep(self, v_list, **kwargs):
        self.disarm()
        self.visa.write(':SYST:TIME:RES')
        self.visa.write(':SOUR:FUNC:MODE VOLT')
        self.visa.write(":SENS:FUNC 'CURR:DC'")
        self.visa.write(":FORM:ELEM VOLT,CURR,TIME")
        if self.auto_range:
            self.visa.write(":SENS:CURR:RANG:AUTO ON")
        else:
            self.visa.write(f":SENS:CURR:RANG {self.sense_range:.2e}")
        if kwargs.get("NPLC", 0):
            self.setNPLC(kwargs['NPLC'])
        self.visa.write(':SOUR:DEL:AUTO ON')
        # self.visa.write(':SOUR:CLE:AUTO ON')
        self.visa.write(f':SOUR:LIST:VOLT {",".join(v_list)}')
        _points = self.visa.query(':SOUR:LIST:VOLT:POIN?')
        if not _points:
            _points = len(v_list)
        self.visa.write(f':TRIG:COUN {_points}')
        self.visa.write(':SOUR:VOLT:MODE LIST')
        self.arm()
        self.visa.write(':INIT')
        return self.visa.get_wait_for_meas()

    def measure_resistance(self):
        self.disarm()
        self.visa.write(':SYST:TIME:RES')
        self.visa.write(':FORM:ELEM RES')
        self.visa.write(":SENS:FUNC 'RES'")
        self.visa.write(':SENS:RES:RANG:AUTO ON')
        self.visa.write(':SENS:RES:MODE AUTO')
        self.arm()
        return self.visa.get_reader()

    def source_with_compliance(self, volts, compliance):
        self.disarm()
        self.visa.write(':SYST:TIME:RES')
        self.visa.write(':FORM:ELEM RES')
        self.visa.write(':SOUR:FUNC:MODE VOLT')
        self.visa.write(":SENS:FUNC 'CURR:DC'")
        self.visa.write(":SENS:CURR:RANG:AUTO ON")
        self.set_compliance(compliance)
        self.visa.write(f":SOUR:VOLT {volts}")
        self.arm()
        self.visa.write(":SYST:LOC")

    def end_voltage_sweep(self, sound=False):
        self.disarm()
        if sound:
            self.visa.playzelda()

    def arm(self):
        self.visa.write(':OUTP ON')
        self.__checkarmed()

    def disarm(self):
        for i in range(0, 10):
            if not self.__checkarmed():
                break
            self.visa.write(':OUTP OFF')
            time.sleep(1)

    def __checkarmed(self):
        try:
            self.output = bool(int(self.visa.query(":OUTP:STAT?")))
        except ValueError:
            return True

    def fetch_data(self):
        # return self.visa.query('FETC?').strip()
        # _data = self.visa.query(':TRAC:DATA?').strip()
        _data = self.visa.query('FETC?').strip()
        self.clearbuffer()
        return _data

    def close(self):
        if self.visa is not None:
            self.visa.close()

    @property
    def armed(self):
        return self.output

class KeithleyV(Instrument):
    """Implement a generic keitheley voltmeter for k2182A
    """

    mode = DEFAULTMODE
    _sense = DEFAULTMODE
    _chan = 1
    sense_range = 0
    auto_range = True
    output = False

    @property
    def sense(self):
        return self._sense

    @sense.setter
    def sense(self, _sense: str):
        self._sense = _sense

    @property
    def chan(self):
        return self._chan

    @chan.setter
    def chan(self, _chan: int):
        self._chan = _chan

    def description(self):
        """ Print a description string to data file"""

        description_string = (
            f"{super().description()}, "
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
            self._sense = VOLT

        elif self.mode == TEMP:
            self._sense = TEMP

        else:
            raise ValueError(f"This mode does exist! Please input {VOLT} or {CURR} only.")
        # self.visa.write_termination = '\n'
        self.data = [0.0, 0.0]
        self.visa.write('*CLS')
        self.visa.write(f":CONF:{self.sense}")
        self.visa.write("INIT:CONT ON")
        self.visa.write("TRIG:SOUR IMM")
        # Switch to medium sampling rate
        self.setNPLC(1)
        # Switch on autozero
        self.visa.write(":SYST:AZER ON")
        # Switch off analog filter
        self.visa.write(f"SENSE:{self.sense}:CHAN{self.chan}:LPAS OFF")
        # Set digital filter window to 5%
        self.visa.write(f"SENSE:{self.sense}:CHAN{self.chan}:DFIL:WIND 5")
        # Set filter counter to 10
        self.visa.write(f"SENSE:{self.sense}:CHAN{self.chan}:DFIL:COUN 10")
        # Switch moving filter on
        self.visa.write(f"SENSE:{self.sense}:CHAN{self.chan}:DFIL:TCON MOV")
        # Switch digital filter on
        self.visa.write(f"SENSE:{self.sense}:CHAN{self.chan}:DFIL:STAT ON")

        return True

    def setNPLC(self, nplc):
        self.visa.write(f':SENSE:{self.sense}:CHAN{self.chan}:NPLC {nplc}')

    def fetch_data(self):
        return self.visa.query('FETC?').strip()

    def read(self):
        return self.visa.query('READ?').strip()

    def close(self):
        if self.visa is not None:
            self.visa.write(':INIT:CONT OFF')
            self.visa.close()

    @property
    def armed(self):
        return self.output
