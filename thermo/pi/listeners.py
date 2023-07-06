# -*- coding: utf-8 -*-
import time
import threading
from multiprocessing.connection import Client, Listener
from thermo.constants import THERMO_PORT, AUTH_KEY, COMMAND_READ, COMMAND_STAT, STAT_OK, STAT_ERROR

COMMAND_RUN = 'RUN'
COMMAND_STOP = 'STOP'

class thermo():

    last_lt = 0.0
    last_rt = 0.0
    last_v = 0.0
    command = COMMAND_RUN
    _lock = threading.Lock()

    def __init__(self, alive, thermocouples={'left':None, 'right':None}, voltmeter=None, **kwargs):
        self.alive = alive
        self.addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', THERMO_PORT))
        self.authkey = kwargs.get('authkey', AUTH_KEY)
        self.voltmeter = voltmeter
        self.lt = thermocouples['left']
        self.rt = thermocouples['right']
        self.__update()

    def start(self):
        """
        Start listening
        """
        # startup the 'listener_main' method as a daemon thread
        self.listener = Listener(address=self.addr, authkey=self.authkey)
        self._listener_thread = threading.Thread(target=self._listener_main, daemon=True)
        self._listener_thread.start()
        self._updater_thread = threading.Thread(target=self._updater_main, daemon=True)
        self._updater_thread.start()

    def stop(self):
        """
        Stops the listening thread
        """
        with Client(self.addr, authkey=self.authkey) as client:
            client.send(COMMAND_STOP)
        self.alive.clear()
        self.command = COMMAND_STOP
        self._listener_thread.join()
        self._updater_thread.join()

    def _listener_main(self):
        """
        The main application loop
        """
        print(f"Starting listener in {self.addr}")
        while self.alive.is_set() and self.command == COMMAND_RUN:
            # block until a client connection is recieved
            with self.listener.accept() as conn:

                # receive the subscription request from the client
                message = conn.recv()

                # if it's a shut down command, return to stop this thread
                if isinstance(message, str) and message == COMMAND_STOP:
                    print(f"Listener {self.addr} dying.")
                    self.alive.clear()
                    self.message = COMMAND_STOP
                    return
                if isinstance(message, str) and message == COMMAND_READ:
                    self.__update()
                    conn.send({'left': self.last_lt,
                               'right': self.last_rt,
                               'voltage': self.last_v})
                if isinstance(message, str) and message == COMMAND_STAT:
                    if self.lt is not None and self.rt is not None:
                        _status = STAT_OK
                    else:
                        _status = STAT_ERROR
                    conn.send({'status': _status})

    def _updater_main(self):
        print("Starting 5 second updater")
        start_time = time.time()
        while self.alive.is_set() and self.command == COMMAND_RUN:
            if time.time() - start_time > 5:
                self.__update()
                start_time = time.time()
            time.sleep(0.1)
        print("Updater thread dying.")
        self.alive.clear()
        self.message = COMMAND_STOP

    def __update(self):
        if self.lt is not None and self.rt is not None:
            try:
                with self._lock:
                    self.last_lt = float(self.lt.temperature)
                    self.last_rt = float(self.rt.temperature)
            except ValueError:
                self.last_lt = -999.99
                self.last_rt = -999.99
        if self.voltmeter is not None:
            time.sleep(0.5)
            try:
                with self._lock:
                    self.last_v = float(self.voltmeter.fetch_data())
            except ValueError as msg:
                print(f"Error reading voltage: {msg}")
                self.last_v = 0.0

    @property
    def lock(self):
        return self._lock

    @property
    def commthread(self):
        return self._listener_thread

    @property
    def updatethread(self):
        return self._updater_thread

    @property
    def lefttemp(self):
        return self.last_lt

    @property
    def righttemp(self):
        return self.last_rt

    @property
    def voltage(self):
        return self.last_v


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

if __name__ == '__main__':
    alive = threading.Event()
    alive.set()
    thermocomm = thermo(alive)
    # voltacomm = volta(alive)
    alive.clear()
         