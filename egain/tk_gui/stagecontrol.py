import time
import logging
import threading
import tkinter.ttk as tk
from tkinter import Toplevel, Text, BooleanVar, StringVar, DoubleVar, Label, messagebox
from tkinter import TOP, BOTTOM, LEFT, RIGHT
from tkinter import END, BOTH, NONE, VERTICAL, HORIZONTAL
from tkinter import DISABLED, NORMAL
from tkinter import X, Y
from .colors import BLACK, WHITE
from egain.stage.backend import NetHost, IP_ADDRESS, PORT
from egain.stage.mks import ESP302
from egain.tk_gui.util import parseusersettings

logger = logging.getLogger(__package__+'.stagecontrol')

class StageControls(tk.Frame):

    Xaxis = 1
    Yaxis = 2
    Zaxis = 3
    axismap = {'up': (Zaxis, 1.0),
               'down': (Zaxis, -1.0),
               'right': (Xaxis, 1.0),
               'left': (Xaxis, -1.0),
               'forward': (Yaxis, -1.0),
               'back': (Yaxis, 1.0)}
    relative_move = 1.0
    unit = 2
    units = {0: 'counts',
             1: 'steps',
             2: 'mm',
             3: 'μm'}
    xyzstage = {'address': IP_ADDRESS,
                'port': PORT,
                'nethost': None,
                'stage': None,
                'initialized': False}
    _isbusy = False
    position = [0.0, 0.0, 0.0]
    widgets = {}  # Holds GUI widgets
    motionControls = {}  # Holds motion control buttons
    cmd_ids = {'error': 0,  # Holds ids for non-blocking queued commands
               'position': 0}
    msg_queue = []  # Hold a queue of messages
    msg_count = 0  # Hold a count of total messages
    config_file = 'StageControls.json'

    def __init__(self, root, **kwargs):
        self.master = root
        self.busy = kwargs.get('busy', BooleanVar(value=False))
        super().__init__(self.master)
        self.relative_move_label = StringVar()
        self.unitStr = StringVar()
        self.config = parseusersettings(self.config_file)
        # self.status = StringVar(value='Nominal')
        self.createWidgets()
        self.alive = threading.Event()
        self.alive.set()

    def __setitem__(self, what, value):
        if what == 'state':
            for key in self.motionControls:
                self.motionControls[key]['state'] = value
            self.widgets['initButton']['state'] = value
        else:
            self.configure(**{what:value})

    @property
    def initialized(self):
        return self.xyzstage['initialized']

    @property
    def isbusy(self):
        return self._isbusy

    def shutdown(self):
        self.alive.clear()

    def createWidgets(self):
        # */ Motion control frame
        xyzFrame = tk.Frame(self)  # Create main xyz motion control frame
        # for _button in self.axismap:  # Create motion control buttons
        #     self.motionControls[_button] = tk.Button(master=xyzFrame,
        #                                              text=_button.capitalize(),
        #                                              command=lambda: self.motionButtonClick(_button),
        #                                              state=DISABLED)
        # NOTE: The code above binds all buttons to lambda: self.motionButtonClick("back") for some reason
        self.motionControls['up'] = tk.Button(master=xyzFrame, text='up'.capitalize(),
                                              command=lambda: self.motionButtonClick('up'), state=DISABLED)
        self.motionControls['down'] = tk.Button(master=xyzFrame, text='down'.capitalize(),
                                                command=lambda: self.motionButtonClick('down'), state=DISABLED)
        self.motionControls['left'] = tk.Button(master=xyzFrame, text='left'.capitalize(),
                                                command=lambda: self.motionButtonClick('left'), state=DISABLED)
        self.motionControls['right'] = tk.Button(master=xyzFrame, text='right'.capitalize(),
                                                 command=lambda: self.motionButtonClick('right'), state=DISABLED)
        self.motionControls['forward'] = tk.Button(master=xyzFrame, text='forward'.capitalize(),
                                                   command=lambda: self.motionButtonClick('forward'), state=DISABLED)
        self.motionControls['back'] = tk.Button(master=xyzFrame, text='back'.capitalize(),
                                                command=lambda: self.motionButtonClick('back'), state=DISABLED)

        relativemoveFrame = tk.Frame(xyzFrame)  # Create frame to hold information about movement
        self.motionControls['scale'] = tk.Scale(master=relativemoveFrame,  # Create slider to set movement distance
                                                from_=1, to=1000,
                                                value=1,
                                                orient=HORIZONTAL,
                                                command=self.relativemoveScaleChange,
                                                state=DISABLED)
        # */ Status frame
        statusFrame = tk.Frame(master=xyzFrame)  # Create frame for status box
        yScroll = tk.Scrollbar(statusFrame, orient=VERTICAL)  # Create yscroller for status box
        self.status = Text(statusFrame, height=3, width=40,  # Create status box
                           bg=WHITE, fg=BLACK, yscrollcommand=yScroll.set)
        yScroll['command'] = self.status.yview  # Attach scroller to status box
        self.status.pack(side=LEFT, fill=BOTH, expand=True)  # Pack the status box
        self.status['state'] = DISABLED  # Disable status box to prevent user input
        yScroll.pack(side=RIGHT, fill=Y)  # Pack the scroll bar
        # Status frame */
        # Motion control frame */
        # */ Relative move frame
        relativemoveLabel = tk.Label(master=relativemoveFrame,  # Create label for slider
                                     text='Relative Move Distance')
        relativemoveindicatorLabel = tk.Label(master=relativemoveFrame,
                                              textvariable=self.relative_move_label)
        self.unitStr.set(self.units[3])  # Set default units to µm
        unitOptionMenu = tk.OptionMenu(relativemoveFrame,  # Create menu for units
                                       self.unitStr,
                                       self.unitStr.get(),
                                       *list(self.units.values()))
        unitOptionMenu['state'] = DISABLED
        self.widgets['unitOptionMenu'] = unitOptionMenu
        # Relative move frame */
        # */ Stage frame
        stageFrame = tk.Frame(master=self)  # Create frame to hold status and position information
        positionFrame = tk.Frame(master=stageFrame)  # Create nexted frame for position information
        gohomebutton = tk.Button(master=positionFrame,  # Create button to initiate home search
                                 text='Go Home',
                                 command=self.gohomeButtonClick,
                                 state=DISABLED)
        self.widgets['gohomebutton'] = gohomebutton  # Store GoHome button
        stagepositionLabel = tk.Label(master=positionFrame, text='Position:')  # Create label for position reporting widgets
        self.widgets['stagepositionvar'] = StringVar(value=str(self.position))  # Create GUI variable to hold position
        stagepositionVal = tk.Label(master=positionFrame,  # Create label to display position variable
                                    textvariable=self.widgets['stagepositionvar'])
        addressFrame = tk.Frame(master=stageFrame)  # Create frame to hold stage address settings
        # Stage frame */
        # */ Address Frame
        stageaddressvar = StringVar(value=self.config.get('IP_ADDRESS', IP_ADDRESS))  # Create GUI variable to hold IP address of stage
        stageportvar = StringVar(value=self.config.get('PORT', PORT))  # Create GUI variable to hold network port of stage
        stageaddressLabel = tk.Label(master=addressFrame, text='Address:')  # Create label for address
        stageaddressEntry = tk.Entry(master=addressFrame,  # Create entry to display address
                                     textvariable=stageaddressvar,
                                     width=12)
        stageportlLabel = tk.Label(master=addressFrame, text='Port:')  # Create label for port
        stageportEntry = tk.Entry(master=addressFrame,  # Create entry to display port
                                  textvariable=stageportvar,
                                  width=4)
        self.xyzstage['address'] = stageaddressvar  # Store stage address as GUI String
        self.xyzstage['port'] = stageportvar  # Store stage network port as GUI String
        initButton = tk.Button(master=addressFrame,  # Create button to initialize stage
                               text='Initialize',
                               command=self.initButtonClick)
        self.widgets['initButton'] = initButton  # Store init button
        self.widgets['stageaddressEntry'] = stageaddressEntry  # Store address entry widget
        self.widgets['stageportEntry'] = stageportEntry  # Store stage port entry widget
        # Address Frame */

        # */ Pack widgets #################################################
        statusFrame.pack(side=BOTTOM)
        relativemoveLabel.pack(side=TOP)
        self.motionControls['scale'].pack(side=TOP)
        relativemoveindicatorLabel.pack(side=TOP)
        relativemoveFrame.pack(side=RIGHT, fill=NONE)
        unitOptionMenu.pack(side=BOTTOM)
        self.motionControls['up'].pack(side=TOP)
        self.motionControls['down'].pack(side=BOTTOM)
        self.motionControls['left'].pack(side=LEFT)
        self.motionControls['right'].pack(side=RIGHT)
        self.motionControls['back'].pack(side=BOTTOM)
        self.motionControls['forward'].pack(side=BOTTOM)
        tk.Separator(positionFrame, orient=HORIZONTAL).pack(side=TOP, fill=X)
        gohomebutton.pack(side=LEFT)
        stagepositionLabel.pack(side=LEFT)
        stagepositionVal.pack(side=LEFT)
        # statusLabel.pack(side=BOTTOM)
        positionFrame.pack(side=TOP)
        stageaddressLabel.pack(side=LEFT)
        stageaddressEntry.pack(side=LEFT)
        stageportlLabel.pack(side=LEFT)
        stageportEntry.pack(side=LEFT)
        addressFrame.pack(side=BOTTOM)
        initButton.pack(side=BOTTOM)
        stageFrame.pack(side=BOTTOM)
        xyzFrame.pack(side=TOP)
        # Pack widgets */ #################################################

    def _saveconfig(self):
        parseusersettings(self.config_file, self.config)

    def _checkformotion(self):
        if self.xyzstage['stage'].isMoving or self.busy.get():
            self.busy.set(True)
            self._isbusy = True
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = DISABLED
            self.widgets['gohomebutton']['state'] = DISABLED
            self._updateposition()
            time.sleep(0.25)
        # self.widgets['initButton'].after('100', lambda: self._waitformotion(self.widgets['initButton']))
        self.widgets['initButton'].after('100', lambda: self._checkformotion)

    def _waitformotion(self, widget):
        if self.xyzstage['stage'].isMoving:
            self.busy.set(True)
            self._isbusy = True
            widget.after('100', lambda: self._waitformotion(widget))
        else:
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = NORMAL
            self.widgets['gohomebutton']['state'] = NORMAL
            self.busy.set(False)
            self._isbusy = False
        self.checkErrors()
        self._updateposition(block=True)

    def initButtonClick(self):
        _address, _port = self.xyzstage['address'].get(), self.xyzstage['port'].get()
        _ok = True
        for _i in _address.split('.'):
            try:
                int(_i)
            except ValueError:
                _ok = False
        try:
            int(_port)
        except ValueError:
            _ok = False
        if len(_address.split('.')) != 4:
            _ok = False
        if _ok:
            self._initstage()
        else:
            messagebox.showerror("Error", "Invalid address settings.")
        self.checkErrors()

    def _initstage(self):
        self.xyzstage['nethost'] = NetHost()
        self.xyzstage['nethost'].initialize(address=self.xyzstage['address'].get(),
                                            port=self.xyzstage['port'].get())
        self.xyzstage['stage'] = ESP302(self.alive, self.xyzstage['nethost'])
        try:
            self.xyzstage['stage'].start()
            self.xyzstage['initialized'] = True
            for _widget in 'initButton', 'stageaddressEntry', 'stageportEntry':
                self.widgets[_widget]['state'] = DISABLED
            self.unitStr.trace_add('write', self._handleunitchange)
            self.relativemoveScaleChange(self.motionControls['scale'].get())
            for _widget in self.motionControls:
                self.motionControls[_widget]['state'] = NORMAL
            for _widget in 'gohomebutton', 'unitOptionMenu':
                self.widgets[_widget]['state'] = NORMAL
            self._handleunitchange()
            self.widgets['initButton'].after(100, self._updateposition)
            self.widgets['initButton'].after(100, self._checkformotion)
            self.config['IP_ADDRESS'] = self.xyzstage['address'].get()
            self.config['PORT'] = self.xyzstage['port'].get()
            self._saveconfig()
        except IOError:
            self.xyzstage['initialized'] = False

    def _updateposition(self, block=False):
        if block:
            self.position = self.xyzstage['stage'].getPosition(block=True)
        else:
            if self.cmd_ids['position'] == 0:
                self.cmd_ids['position'] = self.position = self.xyzstage['stage'].getPosition()
            _res = self.xyzstage['stage'].getresult(self.cmd_ids['position'])
            if _res is False:
                self.widgets['initButton'].after(100, self._updateposition)
                return
            self.position = _res
        self.widgets['stagepositionvar'].set(
            f'{self.position[0]:.2f},{self.position[1]:.2f},{self.position[2]:.2f}')
        self.cmd_ids['position'] = 0

    def checkErrors(self):
        if self.cmd_ids['error'] == 0:
            self.cmd_ids['error'] = self.xyzstage['stage'].getErrors()
        _res = self.xyzstage['stage'].getresult(self.cmd_ids['error'])
        if _res is False:
            self.widgets['initButton'].after(100, self.checkErrors)
            #  self.status.set('Nominal')
            return
        elif _res is not None:
            # self.status.set(_res)
            try:
                self.msg_queue.append(_res.split(',')[2])
            except ValueError:
                self.msg_queue.append('Error reading message buffer.')
            self.msg_count += 1
            self.msg_queue.reverse()
            self.status['state'] = NORMAL
            self.status.delete('1.0', END)
            _i = self.msg_count
            for _msg in self.msg_queue:
                self.status.insert(END, f'{_i}: {_msg}\n')
                _i -= 1
            self.status['state'] = DISABLED
            while len(self.msg_queue) > 10:
                self.msg_queue.pop()
            self.msg_queue.reverse()
        self.cmd_ids['error'] = 0

    def gohomeButtonClick(self):
        for _widget in self.motionControls:
            self.motionControls[_widget]['state'] = DISABLED
        self.widgets['gohomebutton']['state'] = DISABLED
        self.xyzstage['stage'].findHome()
        self.widgets['gohomebutton'].after('100', lambda: self._waitformotion(self.widgets['gohomebutton']))
        self.checkErrors()

    def motionButtonClick(self, _button):
        for _widget in self.motionControls:
            self.motionControls[_widget]['state'] = DISABLED
        self.widgets['gohomebutton']['state'] = DISABLED
        self.motionControls[_button].after('100', lambda: self._waitformotion(self.motionControls[_button]))
        logger.debug(f"*******Moving {_button}:{self.axismap[_button][0]} ({self.axismap[_button][1]*self.relative_move})")
        self.xyzstage['stage'].relativeMove(self.axismap[_button][0], self.axismap[_button][1]*self.relative_move)
        time.sleep(0.25)

    def raiseZaxis(self):
        self.xyzstage['stage'].moveMin(self.Zaxis)
        time.sleep(0.25)
        self._checkformotion()

    def stopZaxis(self):
        self._stopmotion(self.Zaxis)

    def _stopmotion(self, axis):
        _i = 0
        while not self.xyzstage['stage'].stop(axis):
            time.sleep(0.5)
            _i += 1
            if _i > 5:
                break
        self._checkformotion()

    def _handleunitchange(self, *args):
        for key in self.units:
            if self.units[key] == self.unitStr.get():
                self.unit = key
                logger.debug(f"Setting units to {self.units[key]}")
                self.relativemoveScaleChange(self.motionControls['scale'].get())
                self.xyzstage['stage'].setUnits(key)
                time.sleep(1)
                for _unit in self.xyzstage['stage'].getUnits():
                    if _unit != self.unit:
                        logger.warning("Units not set correctly.")
        self._updateposition(block=True)
        self.checkErrors()

    def relativemoveScaleChange(self, distance):
        distance = float(distance)
        if self.unit in (1, 3):
            _distance = f'{distance:.0f}'
            _range = 1000
        else:
            _range = 20
            if distance > _range:
                distance = 0.0
                self.motionControls['scale'].set(distance)
            _distance = f'{distance:.2f}'
        self.motionControls['scale']['to'] = _range

        _labelstring = f'{_distance} {self.units[self.unit]}'
        if abs(distance) > 1 and self.unit == 1:
            _labelstring += 's'
        self.relative_move_label.set(_labelstring)
        self.relative_move = distance

def waitpopup(_label, _time):
    popup = Toplevel()
    popup.geometry('500x100+250-250')
    _msg = StringVar()
    Label(popup, textvariable=_msg).pack()
    prog_var = DoubleVar(value=_time)
    _msg.set(f'{_label} - {_time:.0f}s')
    prog_bar = tk.Progressbar(popup, variable=prog_var, maximum=_time, length=500)
    prog_bar.pack(fill=X)
    t = float(_time)
    while t > 0 and popup.winfo_exists():
        prog_var.set(t)
        _msg.set(f'{_label} - {t:.0f}s')
        popup.update()
        t -= 0.1
        time.sleep(0.1)
    popup.destroy()
