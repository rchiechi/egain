#!/usr/bin/env python3

import os
import sys
import curses
import threading
import time
import platform
from io import StringIO
from meas.k2182A import K2182A
from thermo.peltier import Gradient
from thermo.peltier import _initdevice as init_peltier
from thermo.pi.listeners import thermo
import thermo.constants as tc

try:
    from thermo.pi.seebeck import get_thermocouples, pidisplay
    ON_PI = True
except ModuleNotFoundError:
    ON_PI = False

    def get_thermocouples():
        return None, None

LEFT_ARROW = 260
RIGHT_ARROW = 261
UP_ARROW = 259
DOWN_ARROW = 258
ENTER_KEY = 10
SPACE_KEY = 32
Q_KEY = 113
X_KEY = 120
ON_OFF_MAP = {False: 'OFF', True: 'ON'}

class seebeckstats:

    _initialized = False
    thermothread = None

    def __init__(self, temp_win):
        self.temp_win = temp_win
        self.alive = threading.Event()
        self.display = pidisplay()

    def toggle(self):
        if self.initialized:
            self.stop_pi()
        else:
            self.start_pi()

    def stop_pi(self):
        self.alive.clear()
        if self.thermothread is not None:
            self.thermothread.kill()
        self._initialized = False
        self.display.blank()

    def start_pi(self):
        self.alive.set()
        for _dev in _enumerateDevices('/dev/serial0'):
            voltmeter = K2182A(_dev)
            if voltmeter.initialize(auto_sense_range=True):
                break
            voltmeter = None
        Lthermocouple, Rthermocouple = get_thermocouples()
        self.thermothread = thermo(self.alive, {'left':Lthermocouple, 'right':Rthermocouple}, voltmeter, authkey=tc.AUTH_KEY)
        self.thermothread.start()
        self.display.lock = self.thermothread.lock
        self._initialized = True

    def update(self):
        if self._initialized:
            LT = f"{self.thermothread.lefttemp:0.1f} °C"
            RT = f"{self.thermothread.righttemp:0.1f} °C"
            _v = self.thermothread.voltage
            if abs(_v) < 0.01:
                V = f"Volt.: {_v*1000:0.4f} mV"
            else:
                V = f"Volt.: {_v:0.6f} V"
            self.display.update(LT=LT, RT=RT, V=V)
        else:
            LT = "null"
            RT = 'null'
            V = 'null'
        self.temp_win.addstr(1, 3, 'Right: ')
        self.temp_win.addstr(LT, curses.A_BOLD)
        self.temp_win.addstr('  ')
        self.temp_win.addstr('Left: ')
        self.temp_win.addstr(RT, curses.A_BOLD)
        self.temp_win.addstr(2, 3, 'Volt.: ')
        self.temp_win.addstr(V, curses.A_BOLD)
        self.temp_win.refresh()

    @property
    def initialized(self):
        return self._initialized

class peltierstats:

    _initialized = False
    gradcomm = None

    def __init__(self, grad_win):
        self.grad_win = grad_win
        self.alive = threading.Event()

    def toggle(self):
        if self.initialized:
            self.stop_peltier()
        else:
            self.start_peltier()

    def stop_peltier(self):
        self.alive.clear()
        if self.gradcomm is not None:
            self.gradcomm.stop()
        self._initialized = False

    def start_peltier(self):
        self.alive.set()
        for _dev in _enumerateDevices('ttyACM0'):
            peltier = init_peltier(_dev)
            if peltier is not None:
                break
        if peltier is not None:
            self.gradcomm = Gradient(self.alive, peltier)
            self.gradcomm.start()
            self._initialized = True

    def update(self):
        if not self.initialized:
            self.grad_win.addstr(1, 3, "Not initialized.")
            self.grad_win.refresh()
            return
        # self.grad_win.addstr(1, 3, 'Left: ')
        LT = f"{self.gradcomm.status.get(tc.LEFT, 0.0):0.1f} °C"
        if self.gradcomm.status.get(tc.LEFTFLOW, tc.COOL) == tc.HEAT:
            self.grad_win.addstr(1, 3, 'Left: ', curses.color_pair(250) | curses.A_BOLD)
        elif self.gradcomm.status.get(tc.LEFTFLOW, tc.COOL) == tc.COOL:
            self.grad_win.addstr(1, 3, 'Left: ', curses.color_pair(252) | curses.A_BOLD)
        self.grad_win.addstr(LT, curses.A_BOLD)
        self.grad_win.addstr('  ')
        # self.grad_win.addstr('Right: ')
        RT = f"{self.gradcomm.status.get(tc.RIGHT, 0.0):0.1f} °C"
        if self.gradcomm.status.get(tc.RIGHTFLOW, tc.HEAT) == tc.HEAT:
            self.grad_win.addstr('Right: ', curses.color_pair(250) | curses.A_BOLD)
        elif self.gradcomm.status.get(tc.RIGHTFLOW, tc.HEAT) == tc.COOL:
            self.grad_win.addstr('Right: ', curses.color_pair(252) | curses.A_BOLD)
        self.grad_win.addstr(RT, curses.A_BOLD)
        self.grad_win.refresh()

    @property
    def initialized(self):
        return self._initialized

class menu_idx:

    _idx = 0
    _range = 1

    def _decrement(self):
        self._idx -= 1
        if self._idx < 0:
            self._idx = 0

    @property
    def decrement(self):
        self._decrement()

    def _increment(self):
        self._idx += 1
        if self._idx > self._range:
            self._idx = self._range

    @property
    def increment(self):
        self._increment()

    @property
    def index(self):
        return self._idx

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, _val):
        if _val > 0:
            self._range = _val

def _enumerateDevices(_first=None):
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    if platform.system() == "Linux":
        _filter = 'ttyACM'
    if _first is not None:
        _devs = [_first]
    else:
        _devs = []
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    return _devs


def main(stdscr):
    # external_output = ''
    # stdout_buff = StringIO()
    # sys.stdout = stdout_buff
    # stream_pos = 0  # lst read position of the stdout stream.
    sys.stdout = open('/dev/null', 'wt')
    spinner = [('|', 250), ('\\', 251), ('—', 252), ('/', 253)]
    curses.start_color()
    curses.init_color(250, 1000, 0, 0)
    curses.init_pair(250, 250, curses.COLOR_BLACK)
    curses.init_color(251, 0, 1000, 0)
    curses.init_pair(251, 251, curses.COLOR_BLACK)
    curses.init_color(252, 0, 0, 1000)
    curses.init_pair(252, 252, curses.COLOR_BLACK)
    curses.init_color(253, 1000, 0, 1000)
    curses.init_pair(253, 253, curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.clear()
    stdscr.nodelay(True)
    temp_win = curses.newwin(4, 36, 4, 0)
    thermo_win = seebeckstats(temp_win)
    grad_win = curses.newwin(4, 36, 4, 38)
    pelt_win = peltierstats(grad_win)
    _idx = menu_idx()
    _idx.range = 1
    _menu_map = {0: thermo_win, 1: pelt_win}
    _i = 0
    try:
        while True:
            stdscr.move(0,0)
            _menu_str = f'Turn Seebeck {ON_OFF_MAP[thermo_win.initialized]}'
            if _idx.index == 0:
                stdscr.addstr(_menu_str, curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(_menu_str, curses.A_BOLD)
            stdscr.addstr('     ')
            _menu_str = f'Turn Peltier {ON_OFF_MAP[pelt_win.initialized]}'
            if _idx.index == 1:
                stdscr.addstr(_menu_str, curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(_menu_str, curses.A_BOLD)
            stdscr.clrtoeol()
            if _i == len(spinner):
                _i = 0
            stdscr.addstr(3, 0, f"{spinner[_i][0]}", curses.color_pair(spinner[_i][1]))
            stdscr.refresh()
            time.sleep(0.25)
            temp_win.border()
            grad_win.border()
            thermo_win.update()
            pelt_win.update()
            stdscr.move(10,0)
            # if stdout_buff.tell() > stream_pos:
            #     stdscr.clrtobot()
            #     stdout_buff.seek(stream_pos)
            #     external_output = stdout_buff.read()
            #     stream_pos = stdout_buff.tell()
            #     for _ln, _l in enumerate(external_output.split('\n')):
            #         stdscr.addstr(10+_ln, 0, external_output, curses.A_DIM)
            _i += 1
            _chr = stdscr.getch()
            if _chr == RIGHT_ARROW:
                _idx.increment
            if _chr == LEFT_ARROW:
                _idx.decrement
            if _chr == ENTER_KEY:
                _menu_map[_idx.index].toggle()
                stdscr.clear()
            if _chr in (113, 120):
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        temp_win.clear()
        stdscr.clear()
        thermo_win.stop_pi()
        grad_win.stop_peltier()


if __name__ == "__main__":
    curses.wrapper(main)
    print("\nKilling threads")