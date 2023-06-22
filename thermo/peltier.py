# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import queue
from multiprocessing.connection import Client, Listener
import serial
import json
import platform
import thermo.constants as tc


class Gradient():

    last_json = {}
    last_serial = 0
    _initialized = False
    cmdq = queue.Queue()
    command = tc.COMMAND_RUN
    _lock = threading.Lock()

    def __init__(self, alive, peltier, **kwargs):
        self.alive = alive
        self.peltier = peltier
        self.addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', tc.PELTIER_PORT))
        self.authkey = kwargs.get('authkey', tc.AUTH_KEY)
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
                with self._lock:
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


def _enumerateDevices():
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    if platform.system() == "Linux":
        _filter = 'ttyACM'
    _devs = []
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    # _devs.append(DEFAULTUSBDEVICE)
    return _devs

def _initdevice(device):
    print(f"\nInitializing {device}...", end='')
    n = 0
    try:
        ser_port = os.path.join('/', 'dev', device)
        peltier = serial.Serial(ser_port, 115200, timeout=1)
        _json = ''
        while not _json or n < 10:
            time.sleep(1)
            _json = str(peltier.readline(), encoding='utf8')
            try:
                _msg = json.loads(_json)
                _val = _msg.get('message', '')
                if _val == tc.INITIALIZED:
                    print("\nDevice initalized")
                    time.sleep(0.5)
                    peltier.write(tc.SHOWSTATUS+tc.TERMINATOR)
                    time.sleep(0.5)
                    print("Done!")
                    return peltier
                else:
                    print(_val)
            except json.decoder.JSONDecodeError:
                print(f"{n}...", end='')
                sys.stdout.flush()
            n += 1
    except serial.serialutil.SerialException:
        return None
    print("\nEmpty reply from device.")
    return None


if __name__ == '__main__':
    print("Testing peltier")
    alive = threading.Event()
    alive.set()
    for _dev in _enumerateDevices():
        peltier = _initdevice(_dev)
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