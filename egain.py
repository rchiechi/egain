#!/usr/bin/env python3

from tkinter import Tk
from gui.main import MainFrame
from config.options import Options

root = Tk()
main = MainFrame(root, Options)
root.mainloop()