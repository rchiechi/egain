# -*- coding: utf-8 -*-
import time
from thermo.controllers import Netcontroller

class Thermo(Netcontroller):

    last_lt = 0.0
    last_rt = 0.0
    last_v = 0.0

    def _post_init(self):
        self.lt = self.devices[0]['left']
        self.rt = self.devices[0]['right']
        self.voltmeter = self.devices[1]
        self.last_json = {'left': -999.99,
                          'right': -999.99,
                          'voltage': 0}
        if self.lt is not None and self.rt is not None:
            self._initialized = True
        self.__update()

    @property
    def lefttemp(self):
        return self.last_lt

    @property
    def righttemp(self):
        return self.last_rt

    @property
    def voltage(self):
        return self.last_v

    def _update(self):
        if self.initialized:
            try:
                with self.lock:
                    self.last_json['left'] = float(self.lt.temperature)
                    self.last_json['right'] = float(self.rt.temperature)
            except ValueError:
                self.last_json['left'] = -999.99
                self.last_json['right'] = -999.99
        if self.voltmeter is not None:
            time.sleep(0.5)
            try:
                with self._lock:
                    self.last_json['voltage'] = float(self.voltmeter.fetch_data())
            except ValueError as msg:
                print(f"Error reading voltage: {msg}")
                self.last_json['voltage'] = 0.0
