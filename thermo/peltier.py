# -*- coding: utf-8 -*-
import time
import threading
import thermo.constants as tc
from thermo.util import enumerateDevices, init_thermo_device
from thermo.controllers import Netcontroller

class Gradient(Netcontroller):

    def _post_init(self):
        self._serial_device = self.devices[0]
        print(f'Setting serial device to {self.serial_device}')
        self._update()
        _lt = self.last_json.get(tc.LEFT, None)
        _rt = self.last_json.get(tc.RIGHT, None)
        if _lt is not None:
            self.writeserial(tc.SETLEFTTEMP, float(_lt))
        if _rt is not None:
            self.writeserial(tc.SETRIGHTTEMP, float(_rt))

    def _updater_exit(self):
        self.writeserial(tc.RIGHTOFF)
        time.sleep(0.1)
        self.writeserial(tc.LEFTOFF)

    def _statcheck(self):
        self.writeserial(tc.INIT)
        self._initialized = self.readserial(False).get(tc.INITIALIZED, False)

    def _update(self):
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
            gradcomm = Gradient(alive, peltier, port=tc.PELTIER_PORT)
            gradcomm.start()
            while True:
                time.sleep(1)
                print(gradcomm.status, end='\r')
        except KeyboardInterrupt:
            pass
        gradcomm.stop()
    time.sleep(1)
    alive.clear()