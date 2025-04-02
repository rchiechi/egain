import time
import tkinter.ttk as tk
from tkinter import StringVar
from multiprocessing.connection import Client
import egain.thermo.constants as tc
from egain.tk_gui.util import ping, parseusersettings, validateip

TEMPS = {'LEFT':None, 'RIGHT':None}
DEFAULTUSBDEVICE = 'Choose USB Device'


class Meas(tk.Frame):

    UPDATE_DELAY = 10

    def __init__(self, root):
        self.master = root
        super().__init__(self.master)
        self._lt = 0.0
        self._rt = 0.0
        self._initialized = False
        self.last_status = {}
        self.widgets = {}
        self._host = '127.0.0.1'
        self._port = '6000'
        self.config_file = 'Meas.json'
        _config = parseusersettings(self.config_file)
        self.last_update = time.time() - self.UPDATE_DELAY
        self._ok_to_update = True
        self.post_init()
        self.addr = StringVar(value=f"{_config.get('host', self._host)}:{_config.get('port', self._port)}")
        self.createWidgets()
        self._checkconnetion()
        self.readstatus()
    
    def post_init(self):
        return None

    def createWidgets(self):
        return

    def pause_update(self, *args):
        self._ok_to_update = False

    def unpause_update(self, *args):
        self._ok_to_update = True

    def _checkconnetion(self):
        if not ping(self.host):
            self._initialized = False
            return False
        try:
            with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
                client.send(tc.COMMAND_STAT)
                msg = client.recv()
                if not isinstance(msg, dict):
                    msg = {}
            if msg.get('status', tc.STAT_ERROR) == tc.STAT_OK:
                self._initialized = True
                print("Initialized")
                return True
        except ConnectionRefusedError:
            print(f"Host {self.addr.get().strip()} is down.")
        self._initialized = False
        return False

    def readstatus(self, *args):
        if not self.initialized:
            self.after(5000, self._checkconnetion)
            self.after(6000, self.readstatus)
            return
        try:
            with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
                client.send(tc.COMMAND_READ)
                msg = client.recv()
                if not isinstance(msg, dict):
                    msg = {}
                    self.after(1000, self._checkconnetion)
        except (ConnectionResetError, ConnectionRefusedError):
            self.after(1000, self.readstatus)
            return
        parseusersettings(self.config_file,
                          {'host':self.host, 'port':self.port, 'last_status':msg})
        self.after(1000, self.readstatus)
        self.last_status = msg

    def sendcommand(self, cmd, val=None):
        if not self.initialized:
            return
        try:
            with Client((self.host, self.port), authkey=tc.AUTH_KEY) as client:
                print(f"Sending {tc.COMMAND_SEND}")
                client.send(tc.COMMAND_SEND)
                print(f"Sending: {cmd}, {val}")
                client.send([cmd, val])
                self.last_update = time.time()
        except (ConnectionResetError, ConnectionRefusedError):
            pass

    @property
    def host(self):
        try:
            _addr, _port = self.addr.get().strip().split(':')
            if validateip(_addr):
                return _addr
        except ValueError:
            pass
        return None

    @property
    def port(self):
        try:
            _addr, _port = self.addr.get().strip().split(':')
            return int(_port)
        except ValueError:
            return None

    @property
    def connected(self):
        return self._checkconnetion()

    @property
    def initialized(self):
        return self._initialized
