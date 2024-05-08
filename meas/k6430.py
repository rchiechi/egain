"""
forked from https://github.com/HuangJunye/GrapheneLab-Measurement-Code.git
"""

from .sourcemeter import Keithley

class K6430(Keithley):
    "Class for driving Keithley 6430 Sub-Femptoamp Remove Sourcemeter"

    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)
        self.name = "Keithley 6430"
