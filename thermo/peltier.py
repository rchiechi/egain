# -*- coding: utf-8 -*-
import time
import threading
import queue
from multiprocessing.connection import Client, Listener
import serial
import json
import thermo.constants as tc
from thermo.util import enumerateDevices, init_thermo_device


class Gradient():

    last_json = {}
    last_serial = 0
    _initialized = False
    cmdq = queue.Queue()
    command = tc.COMMAND_RUN
    _lock = threading.Lock()

    def __init__(self, alive=None, peltier=None, **kwargs):
        self._alive = alive
        self._peltier = peltier
        self._addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', tc.PELTIER_PORT))
        self._authkey = kwargs.get('authkey', tc.AUTH_KEY)

    @property
    def alive(self):
        return self._alive

    @alive.setter
    def alive(self, alive):
        self._alive = alive

    @property
    def peltier(self):
        return self._peltier

    @peltier.setter
    def peltier(self, peltier):
        self._peltier = peltier

    @property
    def addr(self):
        return self._addr

    @addr.setter
    def addr(self, addr):
        self._addr = addr

    @property
    def authkey(self):
        return self._authkey

    @authkey.setter
    def authkey(self, authkey):
        self._authkey = authkey

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
        self.__update()

    def stop(self):
        """
        Stops the listening thread
        """
        self.alive.clear()
        self.command = tc.COMMAND_STOP
        with Client(self.addr, authkey=self.authkey) as client:
            client.send(tc.COMMAND_STOP)
        self._listener_thread.join()
        self._updater_thread.join()

    def _listener_main(self):
        """
        The main application loop
        """
        print(f"Starting listener in {self.addr}")
        while self.alive.is_set() and self.command == tc.COMMAND_RUN:
            # block until a client connection is recieved
            with self.listener.accept() as conn:

                # receive the subscription request from the client
                try:
                    message = conn.recv()
                except EOFError:
                    return

                # print(f'Message: {message}')
                # if it's a shut down command, return to stop this thread
                if isinstance(message, str) and message == tc.COMMAND_STOP:
                    print(f"Listener {self.addr} dying.")
                    self.alive.clear()
                    self.message = tc.COMMAND_STOP
                    return

                if isinstance(message, str) and message == tc.COMMAND_READ:
                    # self.__update()
                    conn.send(self.last_json)

                if isinstance(message, str) and message == tc.COMMAND_STAT:
                    if self._initialized:
                        conn.send({'status': tc.STAT_OK})
                    else:
                        conn.send({'status': tc.STAT_ERROR})

                if isinstance(message, str) and message == tc.COMMAND_SEND:
                    try:
                        _cmd = conn.recv()
                    except EOFError:
                        return
                    if isinstance(_cmd, list) and len(_cmd) == 2:
                        self.cmdq.put(_cmd)
                        # self.writeserial(*_cmd)

    def _updater_main(self):
        print("Starting 5 second updater")
        start_time = [time.time(), time.time()]
        while self.alive.is_set() and self.command == tc.COMMAND_RUN:
            if time.time() - start_time[0] > 5:
                self.__update()
                start_time[0] = time.time()
            elif time.time() - start_time[1] > 2:
                self.__statcheck()
                start_time[1] = time.time()
            if not self.cmdq.empty():
                self.writeserial(*self.cmdq.get())
            time.sleep(0.1)

        print("Updater thread dying.")
        self.alive.clear()
        self.message = tc.COMMAND_STOP

    def __statcheck(self):
        self.writeserial(tc.INIT)
        self._initialized = self.readserial(False).get(tc.INITIALIZED, False)

    def __update(self):
        self.writeserial(tc.POLL)
        self.readserial()

    def readserial(self, update=True):
        if time.time() - self.last_serial < 1:
            time.sleep(1)
        try:
            _msg = ''
            _json = {}
            while not _json:
                with self.lock:
                    _msg = str(self.peltier.readline(), encoding='utf8').strip()
                try:
                    _json = json.loads(_msg)
                    if update:
                        self.last_json = _json
                except json.decoder.JSONDecodeError:
                    print(f'JSON Error: "{_msg}"')
        except serial.serialutil.SerialException as msg:
            print(f"Serial error {msg}")
        self.last_serial = time.time()
        return _json

    def writeserial(self, cmd, val=None):
        if time.time() - self.last_serial < 1:
            time.sleep(1)
        if not isinstance(cmd, bytes):
            cmd = bytes(str(cmd), encoding='utf-8')
        if not isinstance(val, bytes) and val is not None:
            val = bytes(str(val), encoding='utf-8')
        try:
            with self.lock:
                self.peltier.write(cmd)
                self.peltier.write(tc.TERMINATOR)
                if val is not None:
                    self.peltier.write(val)
                    self.peltier.write(tc.TERMINATOR)
        except serial.serialutil.SerialException:
            print(f"Error sending command to {self.controller.name}.")
        self.last_serial = time.time()

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
    def status(self):
        return self.last_json

    @property
    def initialized(self):
        return self._initialized


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