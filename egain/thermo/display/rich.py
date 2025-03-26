import sys
import argparse
import threading
import time
from io import StringIO
from egain.meas.k2182A import K2182A
from egain.thermo.peltier import Gradient
from egain.thermo.util import enumerateDevices, init_thermo_device
from egain.thermo.pi.listeners import Thermo
import egain.thermo.constants as tc
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.traceback import Traceback

try:
    from egain.thermo.pi.seebeck import get_thermocouples, pidisplay
    ON_PI = True
except ModuleNotFoundError:
    ON_PI = False

DEVSINUSE = {'peltierstats': None, 'seebeckstats': None}

def update_seebeck_table(lt, rt, v):
    table = Table()
    if abs(v) < 0.01:
        volts = f"{v*1000:0.4f} mV"
    else:
        volts = f"{v:0.6f} V"
    table.add_column("[b]Left")
    table.add_column("[b]Right")
    table.add_column("[b]ΔV")
    table.add_row(f"{lt:0.1f} °C", f"{rt:0.1f} °C", volts)
    return table

def update_peltier_table(lt, rt, lm, rm):
    table = Table()
    if lm == tc.HEAT:
        left = "[b][red]Left"
    elif lm == tc.COOL:
        left = "[b][blue]Left"
    else:
        left = "[b]Left"
    if rm == tc.HEAT:
        right = "[b][red]Right"
    elif rm == tc.COOL:
        right = "[b][blue]Right"
    else:
        right = "[b]Right"
    table.add_column(left)
    table.add_column(right)
    table.add_row(f"{lt:0.1f} °C", f"{rt:0.1f} °C")
    return table

def gui(opts):
    # Create layout
    layout = Layout()
    layout.split_row(
        Layout(name="seebeck"),
        Layout(name="peltier")
    )
    console = Console()
    alive = threading.Event()
    alive.set()
    thermothread, gradcomm = None, None
    if opts.seebeck:
        voltmeter = None
        console.print("[b][yellow]Starting seebeck... ", end='')
        for dev in enumerateDevices(first='serial0'):
            if dev in DEVSINUSE.values():
                continue
            voltmeter = K2182A(dev)
            if voltmeter.initialize(auto_sense_range=True):
                DEVSINUSE['seebeckstats'] = dev
                break
            voltmeter = None
        if voltmeter:
            Lthermocouple, Rthermocouple = get_thermocouples()
            thermothread = Thermo(alive,
                                [{'left':Lthermocouple, 'right':Rthermocouple}, voltmeter],
                                    port=tc.THERMO_PORT,
                                    console=console)
            thermothread.start()
            console.print(f"[green]started on {dev}.")
        else:
            console.print("[b][red]Error starting seebeck.")
    
    if opts.peltier:
        peltier = None
        console.print("[b][yellow]Starting peltier... ", end='')
        for dev in enumerateDevices(first='ttyACM0'):
            if dev in DEVSINUSE.values():
                continue
            peltier = init_thermo_device(dev)
            if peltier is not None:
                DEVSINUSE['peltierstats'] = dev
                break
        if peltier:
            gradcomm = Gradient(alive, peltier, port=tc.PELTIER_PORT, console=console)
            gradcomm.start()
            console.print(f"[green]started on {dev}.")
        else:
            console.print("[b][red]Error starting peltier.")
    try:
        
        layout["seebeck"].update(update_seebeck_table(0, 0, 0))
        layout["peltier"].update(update_peltier_table(0, 0, None, None))
        
        with Live(layout, refresh_per_second=4) as live:
            while True:                
                if thermothread:
                    lts =thermothread.lefttemp
                    rts = thermothread.righttemp
                    voltage = thermothread.voltage
                    layout["seebeck"].update(update_seebeck_table(lts, rts, voltage))
                if gradcomm:
                    ltp = gradcomm.status.get(tc.LEFT, 0.0)
                    rtp = gradcomm.status.get(tc.RIGHT, 0.0)
                    lm = gradcomm.status.get(tc.LEFTFLOW)
                    rm = gradcomm.status.get(tc.RIGHTFLOW)
                    layout["peltier"].update(update_peltier_table(ltp, rtp, lm, rm))
                time.sleep(0.5)    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        layout["seebeck"].update(f"Exception: {e}")
        layout["peltier"].update(Panel(Traceback.from_exception(type(e), e, e.__traceback__)))
        raise(e)
    finally:
        alive.clear()