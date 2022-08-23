import os
import platform
import logging
import threading
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, Listbox, Label, Entry
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import

    
class StageControls(tk.Frame):
    
    def createWidgets(self):
        xyzFrame = tk.Frame(self)
        # commandFrame = tk.Frame(self)

        upButton = tk.Button(master=xyzFrame, text="Up", command=upButtonClick)
        downButton = tk.Button(master=xyzFrame, text="Down", command=downButtonClick)
        leftButton = tk.Button(master=xyzFrame, text="Left", command=leftButtonClick)
        rightButton = tk.Button(master=xyzFrame, text="Right", command=rightButtonClick)
        forwardButton = tk.Button(master=xyzFrame, text="Forward", command=forwardButtonClick)
        backButton = tk.Button(master=xyzFrame, text="Back", command=backButtonClick)
        
        upButton.pack(side=TOP)
        downButton.pack(side=BOTTOM)
        leftButton.pack(side=LEFT)
        rightButton.pack(side=RIGHT)
        backButton.pack(side=BOTTOM)
        forwardButton.pack(side=BOTTOM)

        
        xyzFrame.pack(side=TOP)
        # commandFrame.pack(side=BOTTOM)
        print("Yo")


def upButtonClick():
    return

def downButtonClick():
    return

def leftButtonClick():
    return

def rightButtonClick():
    return

def forwardButtonClick():
    return

def backButtonClick():
    return