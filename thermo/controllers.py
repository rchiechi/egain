# -*- coding: utf-8 -*-
import time
import threading
import queue
from multiprocessing.connection import Client, Listener
import serial
import json
import thermo.constants as tc

class Netcontroller():

    last_json = {}
    last_serial = 0
    _initialized = False
    cmdq = queue.Queue()
    command = tc.COMMAND_RUN
    _lock = threading.Lock()
    _serial_device = None
    _listener_thread = None
    _updater_thread = None
    listener = None

    def __init__(self, alive=None, devices=None, **kwargs):
        self._alive = alive
        self._devices = devices if isinstance(devices, list) else [devices]
        self._addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', 6000))
        self._authkey = kwargs.get('authkey', tc.AUTH_KEY)
        self._post_init()

    def _post_init(self):
        return None

    @property
    def alive(self):
        return self._alive

    @alive.setter
    def alive(self, alive):
        self._alive = alive

    @property
    def devices(self):
        return self._devices

    @property
    def serial_device(self):
        return self._serial_device

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
        self._update()

    def stop(self):
        """
        Stops the listening thread
        """
        self._initialized = False
        if self.alive.is_set():
            self.alive.clear()
            self.command = tc.COMMAND_STOP
            _addr = self.addr if self.addr[0] != '0.0.0.0' else '127.0.0.1'
            with Client((_addr, self.addr[1]), authkey=self.authkey) as client:
                client.send(tc.COMMAND_STOP)
            self._listener_thread.join()
            self._updater_thread.join()

    def _listener_main(self):
        """
        The main application loop
        """
        print(f"Starting listener in {self.addr}")
        while self.alive.is_set() and self.command == tc.COMMAND_RUN:
            # block until a client connection is received
            with self.listener.accept() as conn:
                # receive the subscription request from the client
                try:
                    message = conn.recv()
                except EOFError:
                    return
                # if it's a shut down command, return to stop this thread
                if isinstance(message, str) and message == tc.COMMAND_STOP:
                    print(f"Listener {self.addr} dying.")
                    self.alive.clear()
                    self.message = tc.COMMAND_STOP
                    return

                if isinstance(message, str) and message == tc.COMMAND_READ:
                    conn.send(self.last_json)

                if isinstance(message, str) and message == tc.COMMAND_STAT:
                    if self.initialized:
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

    def _updater_main(self):
        print("Starting 5 second updater")
        start_time = [time.time(), time.time()]
        while self.alive.is_set() and self.command == tc.COMMAND_RUN:
            if time.time() - start_time[0] > 5:
                self._update()
                start_time[0] = time.time()
            elif time.time() - start_time[1] > 2:
                self._statcheck()
                start_time[1] = time.time()
            if not self.cmdq.empty():
                self.writeserial(*self.cmdq.get())
            time.sleep(0.1)
        self._updater_exit()
        print("Updater thread dying.")
        self.alive.clear()
        self.message = tc.COMMAND_STOP

    def _updater_exit(self):
        return None

    def _statcheck(self):
        return None

    def _update(self):
        return None

    def readserial(self, update=True):
        if time.time() - self.last_serial < 1:
            time.sleep(1)
        try:
            _msg = ''
            _json = {}
            while not _json:
                with self.lock:
                    _msg = str(self.serial_device.readline(), encoding='utf8').strip()
                try:
                    _json = json.loads(_msg)
                    if update:
                        self.last_json = _json
                except json.decoder.JSONDecodeError:
                    print(f'JSON Error: "{_msg}"')
        except serial.serialutil.SerialException as msg:
            print(f"Serial error {msg}")
        except AttributeError:
            print("Error reading. Serial device not connected")
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
                self.serial_device.write(cmd)
                self.serial_device.write(tc.TERMINATOR)
                if val is not None:
                    self.serial_device.write(val)
                    self.serial_device.write(tc.TERMINATOR)
        except serial.serialutil.SerialException:
            print(f"Error sending command to {self.serial_device.name}.")
        except AttributeError as msg:
            print(f"Error sending {cmd}. Serial device not connected: {msg}")
        self.last_serial = time.time()
