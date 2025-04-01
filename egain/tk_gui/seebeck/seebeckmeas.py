import tkinter.ttk as tk
from tkinter import StringVar
from tkinter import N
from tkinter import TOP, LEFT, RIGHT  # pylint: disable=unused-import
import egain.thermo.constants as tc
from .meas import Meas


class SeebeckMeas(Meas):

    def post_init(self):
        self._port = tc.THERMO_PORT
        self._v = 0.0
        self.config_file = 'SeebeckMeas.json'

    def createWidgets(self):
        self.left_temp_reading = StringVar(value='0.0')
        self.right_temp_reading = StringVar(value='0.0')
        self.voltage_reading = StringVar(value='0.0')
        tempFrame = tk.LabelFrame(self,
                                  text='Surface Temperatures (°C)',
                                  labelanchor=N)
        tk.Label(tempFrame,
                 padding=5,
                 text='Left: ').pack(side=LEFT)
        tk.Label(tempFrame,
                 padding=5,
                 textvariable=self.left_temp_reading).pack(side=LEFT)
        tk.Label(tempFrame,
                 padding=5,
                 textvariable=self.right_temp_reading).pack(side=RIGHT)
        tk.Label(tempFrame,
                 padding=5,
                 text='Right: ').pack(side=RIGHT)
        voltFrame = tk.LabelFrame(self,
                                  text='Surface Voltage (V)',
                                  labelanchor=N)
        tk.Label(voltFrame,
                 textvariable=self.voltage_reading).pack(side=TOP)
        deviceFrame = tk.LabelFrame(self,
                                    text='Device Settings',
                                    labelanchor=N)
        tk.Label(deviceFrame,
                 text='Address:').pack(side=LEFT)
        tk.Entry(deviceFrame,
                 width=15,
                 textvariable=self.addr).pack(side=LEFT)
        tempFrame.pack(side=TOP)
        voltFrame.pack(side=TOP)
        deviceFrame.pack(side=TOP)
        self.readtemps()

    def readtemps(self, *args):
        self._lt = self.last_status.get('left', -999.99)
        self._rt = self.last_status.get('right', -999.99)
        self._v = self.last_status.get('voltage', 0.0)
        self.left_temp_reading.set(f'{self._lt:0.2f}')
        self.right_temp_reading.set(f'{self._rt:0.2f}')
        self.voltage_reading.set(f'{self._v:0.4f}')
        self.after(250, self.readtemps)

    @property
    def voltage(self):
        return self._v

    @property
    def temps(self):
        self.readtemps()
        return {'left': self._lt, 'right': self._rt}
