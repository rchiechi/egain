# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
from multiprocessing.connection import Client, Listener
import serial
import json
import platform
from .constants import *

COMMAND_RUN = 'RUN'
COMMAND_STOP = 'STOP'

class Gradient():

    last_json = {}
    command = COMMAND_RUN
    _lock = threading.Lock()

    def __init__(self, alive, peltier, **kwargs):
        self.alive = alive
        self.peltier = peltier
        self.addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', PELTIER_PORT))
        self.authkey = kwargs.get('authkey', AUTH_KEY)
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
        self.command = COMMAND_STOP
        with Client(self.addr, authkey=self.authkey) as client:
            client.send(COMMAND_STOP)
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
                    conn.send(self.last_json)

                if isinstance(message, str) and message == COMMAND_STAT:
                    conn.send({'status': self.__statcheck()})

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

    def __statcheck(self):
        self.writeserial(INIT)
        return self.readserial(False).get(INITIALIZED, False)

    def __update(self):
        self.writeserial(POLL)
        self.readserial()

    def readserial(self, update=True):
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
                except json.decoder.JSONDecodeError as err:
                    print(f'JSON Error: {err}')
        except serial.serialutil.SerialException as msg:
            print(f"Serial error {msg}")
        return _json

    def writeserial(self, cmd, val=None):
        if not isinstance(cmd, bytes):
            cmd = bytes(cmd, encoding='utf-8')
        if not isinstance(val, bytes) and val is not None:
            cmd = bytes(val, encoding='utf-8')
        try:
            with self.lock:
                self.peltier.write(cmd+TERMINATOR)
                if val is not None:
                    self.controller.write(val+TERMINATOR)
        except serial.serialutil.SerialException:
            print(f"Error sending command to {self.controller.name}.")

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
                if _val == INITIALIZED:
                    print("\nDevice initalized")
                    time.sleep(0.5)
                    peltier.write(SHOWSTATUS+TERMINATOR)
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
        gradcomm = Gradient(alive, peltier)
        gradcomm.start()
        print(gradcomm.status)
        gradcomm.stop()
    alive.clear()