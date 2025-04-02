#!/usr/bin/env python3

import sys
import argparse
import traceback
from egain.thermo.display import cursesgui, richgui

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
subparsers = parser.add_subparsers(dest="mode", help="sub-command help")
rich_parser = subparsers.add_parser('rich', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
curses_parser = subparsers.add_parser('curses', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
rich_parser.add_argument('--seebeck', action="store_true",
                             help="Startup with seebeck active.")
rich_parser.add_argument('--peltier', action="store_true",
                              help="Startup with peltier active.")
rich_parser.add_argument('--dummy', action="store_true",
                                help="Startup with dummy controllers.")
opts = parser.parse_args()
try:
    if opts.mode == 'curses':
        cursesgui(opts)
    elif opts.mode == 'rich':
        richgui(opts)
    else:
        parser.print_help()
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
finally:
    print("\nKilling threads") 