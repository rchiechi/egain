#!/usr/bin/env python3

import os
import curses
import threading
import time
import platform
from meas.k2182A import K2182A
from thermo.peltier import Gradient
from thermo.pi.listeners import thermo
from thermo.pi.seebeck import get_thermocouples, pidisplay
import thermo.constants as tc


def _enumerateDevices():
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    if platform.system() == "Linux":
        _filter = 'ttyACM'
    _devs = ['/dev/serial0']
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    return _devs

def init_pi():
    alive = threading.Event()
    alive.set()
    for _dev in _enumerateDevices():
        voltmeter = K2182A(_dev)
        if voltmeter.initialize(auto_sense_range=True):
            break
        voltmeter = None
    Lthermocouple, Rthermocouple = get_thermocouples()
    thermothread = thermo(alive, {'left':Lthermocouple, 'right':Rthermocouple}, voltmeter, authkey=tc.AUTH_KEY)
    thermothread.start()
    return alive, thermothread

def main(stdscr):
    spinner = [('|', 250), ('\\', 251), ('—', 252), ('/', 253)]
    curses.start_color()
    # use 250 to not interfere with tests later
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
    temp_win = curses.newwin(4, 36, 2, 0)
    temp_win.border()
    _i = 0
    try:
        while True:
            if _i == len(spinner):
                _i = 0
            stdscr.addstr(0, 0, f"{spinner[_i][0]}", curses.color_pair(spinner[_i][1]))
            stdscr.refresh()
            LT = f"Left: {thermothread.lefttemp:0.1f} °C"
            RT = f"Right: {thermothread.righttemp:0.1f} °C"
            _v = thermothread.voltage
            if abs(_v) < 0.01:
                V = f"Volt.: {_v*1000:0.4f} mV"
            else:
                V = f"Volt.: {_v:0.6f} V"
            temp_win.addstr(1, 3, LT, curses.A_BOLD)
            temp_win.addstr('  ')
            temp_win.addstr(RT, curses.A_BOLD)
            temp_win.addstr(2, 3, V, curses.A_BOLD)
            temp_win.refresh()
            _i += 1
            pidisplay(thermothread.lock, LT=LT, RT=RT, V=V)
            if stdscr.getch() in (113, 120):
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        temp_win.clear()
        stdscr.clear()


if __name__ == "__main__":
    alive, thermothread = init_pi()
    curses.wrapper(main)
    print("\nKilling threads")
    thermothread.stop()
    alive.clear()