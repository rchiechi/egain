#!/usr/bin/env python3

from tkinter import Tk
from gui.main import MainFrame
from config.options import createOptions

root = Tk()
main = MainFrame(root, createOptions())
root.mainloop()