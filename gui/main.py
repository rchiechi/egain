'''
Copyright (C) 2022 Ryan Chiechi <ryan.chiechi@ncsu.edu>
Description:

        This is the GUI front-end for the parsing engine. It mostly works ok,
        but some of the options configurable on the command line may not be
        implemented.

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os
import platform
import logging
import threading
import tkinter.ttk as tk
from tkinter import Tk
# from tkinter import Toplevel
from tkinter import filedialog
from tkinter import Text, IntVar, StringVar, Listbox, Label
from tkinter import N, S, E, W, X, Y  # pylint: disable=unused-import
from tkinter import TOP, BOTTOM, LEFT, RIGHT  # pylint: disable=unused-import
from tkinter import END, BOTH, VERTICAL, HORIZONTAL  # pylint: disable=unused-import
from tkinter import EXTENDED, RAISED, DISABLED, NORMAL  # pylint: disable=unused-import
from tkinter import PhotoImage
from tkinter.font import Font
from gui.colors import BLACK, YELLOW, WHITE, RED, TEAL, GREEN, BLUE, GREY  # pylint: disable=unused-import
from gui.datacanvas import dataCanvas

absdir = os.path.dirname(os.path.realpath(__file__))

class MainFrame(tk.Frame):
    '''The main frame for collecting EGaIn data.'''
    def __init__(self, root, opts):
        self.root = root
        super().__init__(self.root)
        self.opts = opts
        bgimg = PhotoImage(file=os.path.join(absdir, 'RCCLabFluidic.png'))
        limg = Label(self.root, i=bgimg, background=GREY)
        limg.pack(side=TOP)
        self.root.title("RCCLab EGaIn Data Parser")
        self.root.geometry('800x850+250+250')
        self.pack(fill=BOTH)
        self.__createWidgets()
        self.ToFront()
        
    def ToFront(self):
        '''Try to bring the main window to the front on different platforms'''
        if platform.system() == "Darwin":
            os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
        else:
            self.master.attributes('-topmost', 1)
            self.master.attributes('-topmost', 0)
        self.master.lift()
        
        
    def __createWidgets(self):
        self.buttonFrame = tk.Frame(self)
        self.stagecontrolFrame = tk.Frame(self)
        self.dataFrame = tk.Frame(self)

        
        self.dataCanvas = dataCanvas(self.dataFrame)
        
        self.quitButton = tk.Button(master=self.buttonFrame, text="Quit", command=self.root.quit)
        
        self.dataFrame.pack(side=TOP, fill=BOTH)
        self.stagecontrolFrame.pack(side=BOTTOM, fill=None)
        self.buttonFrame.pack(side=BOTTOM, fill=X)
        
        