# -*- coding: utf-8 -*-
import time
import threading
import thermo.constants as tc
from thermo.util import enumerateDevices, init_thermo_device
from thermo.controllers import Netcontroller

class Gradient(Netcontroller):

    def _post_init(self):
        self._serial_device = self.devices[0]

    def _updater_exit(self):
        self.writeserial(tc.RIGHTOFF)
        time.sleep(0.1)
        self.writeserial(tc.LEFTOFF)

    def __statcheck(self):
        self.writeserial(tc.INIT)
        self._initialized = self.readserial(False).get(tc.INITIALIZED, False)

    def __update(self):
        self.writeserial(tc.POLL)
        self.readserial()


if __name__ == '__main__':
    print("Testing peltier")
    alive = threading.Event()
    alive.set()
    for _dev in enumerateDevices():
        peltier = init_thermo_device(_dev)
        if peltier is not None:
            break
    if peltier is not None:
        try:
            gradcomm = Gradient(alive, peltier)
            gradcomm.start()
            while True:
                time.sleep(1)
                # print(gradcomm.status, end='\r')
        except KeyboardInterrupt:
            pass
        gradcomm.stop()
    time.sleep(1)
    alive.clear()