#!/usr/bin/env python3

import os
import sys
from tkinter import Tk
BIN = os.path.basename(sys.argv[0])
if 'egain' in BIN:
    from gui.main.egain import MainFrame
elif 'seebeck' in BIN:
    from gui.main.seebeck import MainFrame
else:
    print(f"Call this script from a symlink with either egain or seebeck in the name, not {BIN}.")
    sys.exit()

root = Tk()
main = MainFrame(root)
root.mainloop()
