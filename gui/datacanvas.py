import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np


class dataCanvas(FigureCanvasTkAgg):

    def __init__(self, root):
        fig = Figure(figsize=(5, 4), dpi=100)
        t = np.arange(0, 3, .01)
        self.ax = fig.add_subplot()
        line, = self.ax.plot(t, 2 * np.sin(2 * np.pi * t))
        self.ax.set_xlabel("Voltage")
        self.ax.set_ylabel("Current")
        self.canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
        self.canvas.draw()

        # pack_toolbar=False will make it easier to use a layout manager later on.
        toolbar = NavigationToolbar2Tk(self.canvas, root, pack_toolbar=False)
        toolbar.update()

        self.canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)

        # button_quit = tkinter.Button(master=root, text="Quit", command=root.quit)

        def update_frequency(new_val):
            # retrieve frequency
            f = float(new_val)

            # update data
            y = 2 * np.sin(2 * np.pi * f * t)
            line.set_data(t, y)
            # required to update canvas and attached toolbar!
            self.canvas.draw()

        #  slider_update = tkinter.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL,
                                      # command=update_frequency, label="Frequency [Hz]")

        # Packing order is important. Widgets are processed sequentially and if there
        # is no space left, because the window is too small, they are not displayed.
        # The canvas is rather flexible in its size, so we pack it last which makes
        # sure the UI controls are displayed as long as possible.
        # button_quit.pack(side=tkinter.BOTTOM)
        # slider_update.pack(side=tkinter.BOTTOM)
        toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    def displayData(self, data):
        self.ax.cla()
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Current (I)")
        self.ax.plot('V', 'I', '', data=data)
        self.canvas.draw()
