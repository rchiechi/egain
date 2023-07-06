# -*- coding: utf-8 -*-
import time
from thermo.controllers import Netcontroller

class Thermo(Netcontroller):

    last_lt = 0.0
    last_rt = 0.0
    last_v = 0.0

    def _post_init__(self):
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

#     def _listener_main(self):
#         """
#         The main application loop
#         """
#         print(f"Starting listener in {self.addr}")
#         while self.alive.is_set() and self.command == tc.COMMAND_RUN:
#             # block until a client connection is recieved
#             with self.listener.accept() as conn:
# 
#                 # receive the subscription request from the client
#                 message = conn.recv()
# 
#                 # if it's a shut down command, return to stop this thread
#                 if isinstance(message, str) and message == tc.COMMAND_STOP:
#                     print(f"Listener {self.addr} dying.")
#                     self.alive.clear()
#                     self.message = tc.COMMAND_STOP
#                     return
#                 if isinstance(message, str) and message == tc.COMMAND_READ:
#                     self.__update()
#                     conn.send({'left': self.last_lt,
#                                'right': self.last_rt,
#                                'voltage': self.last_v})
#                 if isinstance(message, str) and message == tc.COMMAND_STAT:
#                     if self.lt is not None and self.rt is not None:
#                         _status = tc.STAT_OK
#                     else:
#                         _status = tc.STAT_ERROR
#                     conn.send({'status': _status})
# 
#     def _updater_main(self):
#         print("Starting 5 second updater")
#         start_time = time.time()
#         while self.alive.is_set() and self.command == tc.COMMAND_RUN:
#             if time.time() - start_time > 5:
#                 self.__update()
#                 start_time = time.time()
#             time.sleep(0.1)
#         print("Updater thread dying.")
#         self.alive.clear()
#         self.message = tc.COMMAND_STOP

    def __update(self):
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



# class volta(threading.Thread):

#     last_v = 0.0

#     def __init__(self, alive, smu={'voltmeter':None}, **kwargs):
#         super().__init__()
#         self.alive = alive
#         self.addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', VOLTA_PORT))
#         self.authkey = kwargs.get('authkey', b'1234')
#         self.lt = thermocouples['left']
#         self.rt = thermocouples['right']

#     def run(self):
#         print(f"Starting listener in {self.addr}")
#         listener = Listener(self.addr, authkey=self.authkey)
#         while self.alive.is_set():
#             with listener.accept() as conn:
#                 msg = conn.recv()
#                 if msg == 'close':
#                     conn.close()
#                     self.kill()
#                     break
#                 if msg == 'read':
#                     self.sendtemps(conn)
#         listener.close()

#     def kill(self):
#         print(f"{self.name} dying.")
#         self.alive.clear()

#     def sendvoltage(self, conn):
#         return

#     @property
#     def voltage(self):
#         return self.last_v


# if __name__ == '__main__':
#     alive = threading.Event()
#     alive.set()
#     thermocomm = Thermo(alive)
#     # voltacomm = volta(alive)
#     alive.clear()
