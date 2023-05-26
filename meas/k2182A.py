"""
forked from https://github.com/HuangJunye/GrapheneLab-Measurement-Code.git
"""

from .sourcemeter import KeithleyV

class K2182A(KeithleyV):
    "Class for driving Keithley 2182A Nanovolt Remove Meter"

    def __init__(self, address):
        super().__init__(address)
        self.name = "Keithley 6430"
