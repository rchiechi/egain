# -*- coding: utf-8 -*-
import time
import threading
import queue
from multiprocessing.connection import Client, Listener
import serial
import json
from . import constants as tc
from rich.console import Console


    

class Netcontroller:

    def __init__(self, alive=None, devices=None, **kwargs):
        self._lock = threading.Lock()
        self.console = kwargs.get('console', Console())
        self._update_frequency = 5
        self._statcheck_frequency = 5
        self.last_json = {}
        self.last_serial = 0
        self._initialized = False
        self.cmdq = queue.Queue()
        self.command = tc.COMMAND_RUN
        self._serial_device = None
        self._listener_thread = None
        self._updater_thread = None
        self.listener = None
        self._alive = alive
        self._devices = devices if isinstance(devices, list) else [devices]
        self._addr = (kwargs.get('address', '0.0.0.0'), kwargs.get('port', 6000))
        self._authkey = kwargs.get('authkey', tc.AUTH_KEY)
        self._post_init()

    def _post_init(self):
        return None

    @property
    def update_frequency(self):
        return self._update_frequency

    @update_frequency.setter
    def update_frequency(self, _freq: float):
        if _freq > 0:
            self._update_frequency = _freq

    @property
    def statcheck_frequency(self):
        return self._statcheck_frequency

    @statcheck_frequency.setter
    def statcheck_frequency(self, _freq: float):
        if _freq > 0:
            self._statcheck_frequency = _freq

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
        self.console.print(f"Starting listener in {self.addr}")
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
                    self.console.print(f"Listener {self.addr} dying.")
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
        self.console.print(f"Starting {self.update_frequency} second updater with ")
        self.console.print(f"statcheck upates at {self.statcheck_frequency} seconds.")
        start_time = [time.time(), time.time()]
        while self.alive.is_set() and self.command == tc.COMMAND_RUN:
            if time.time() - start_time[0] > self.update_frequency:
                self._update()
                start_time[0] = time.time()
            elif time.time() - start_time[1] > self.statcheck_frequency:
                self._statcheck()
                start_time[1] = time.time()
            if not self.cmdq.empty():
                self.writeserial(*self.cmdq.get())
            time.sleep(0.1)
        self._updater_exit()
        self.console.print("Updater thread dying.")
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
                    self.console.print(f'JSON Error: "{_msg}"')
                    self.serial_device.timeout = 500
                    _c = b'1'
                    while _c:  # Purge serial bufffer
                        _c = self.serial_device.read(1)
        except serial.serialutil.SerialException as msg:
            self.console.print(f"Serial error {msg}")
        except AttributeError:
            self.console.print("Error reading. Serial device not connected")
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
            self.console.print(f"Error sending command to {self.serial_device.name}.")
        except AttributeError:
            self.console.print(f"Error sending {cmd}. Serial device not connected.")
        self.last_serial = time.time()

class Dummycontroller(Netcontroller):

    def post_init(self):
        self._initialized = True
        self.lt = None
        self.rt = None
        self.voltmeter = None
        for attribute in dir(tc):
            if not attribute.startswith('_'):  # Skip private attributes
                value = getattr(tc, attribute)
                self.last_json[str(value)] = None
        self.last_json = {'left': -999.99,
                          'right': -999.99,
                          'voltage': 0}

    def readserial(self, update=True):
        self.last_serial = time.time()
        return self.last_json

    def writeserial(self, cmd, val=None):
        self.console.print(Panel(f"cmd: {cmd}, val:{val}", title='Dummycontroller'))
        self.last_json[str(cmd)] = val
        self.last_serial = time.time()

    @property
    def lefttemp(self):
        return self.last_json['left']

    @property
    def righttemp(self):
        return self.last_json['right']

    @property
    def voltage(self):
        return self.last_json['voltage']