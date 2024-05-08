#!/usr/bin/env python3

import os
import sys
import logging
from config.logging import ColorFormatter
from config.options import parsecliopts
from tkinter import Tk

# _logfile = os.path.join(TMPDIR, os.path.basename(sys.argv[0]).split('.')[0] + '.log')
# loghandler = logging.FileHandler(_logfile)
# loghandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s'))
# logger.addHandler(loghandler)
cli_opts = parsecliopts()
logger = logging.getLogger(__package__)
_level = logging.INFO
if cli_opts.debug:
    _level = logging.DEBUG
logger.setLevel(_level)
streamhandler = logging.StreamHandler()
streamhandler.setFormatter(ColorFormatter())
logger.addHandler(streamhandler)
# logger.info("Logging to %s", _logfile)
logging.getLogger("matplotlib").setLevel(logging.WARN)
logging.getLogger("PIL").setLevel(logging.WARN)
logger.debug("Debug logging enabled.")
# logging.debug("Logging to %s", _logfile)

BIN = os.path.basename(sys.argv[0])
if 'egain' in BIN:
    from gui.main.egain import MainFrame
elif 'seebeck' in BIN:
    from gui.main.seebeck import MainFrame
else:
    print(f"Call this script from a symlink with either egain or seebeck in the name, not {BIN}.")
    sys.exit()


root = Tk()
main = MainFrame(root, cli_opts)
root.mainloop()
