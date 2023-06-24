# -*- coding: utf-8 -*-
try:
    import digitalio
    import board
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import sys
    print("Make sure you are running this script on a Raspberry Pi")
    sys.exit()
import os
import time
import subprocess
import threading
import curses
import platform
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
import adafruit_max31856
from .listeners import thermo
from meas.k2182A import K2182A
import thermo.constants as tc

led = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)

# Create sensor object, communicating over the board's default SPI bus
spi = board.SPI()

# allocate a CS pin and set the direction
Lcs = digitalio.DigitalInOut(board.D5)
Lcs.direction = digitalio.Direction.OUTPUT
Rcs = digitalio.DigitalInOut(board.D6)
Rcs.direction = digitalio.Direction.OUTPUT

# create a thermocouple object with the above
Lthermocouple = adafruit_max31856.MAX31856(spi, Lcs, thermocouple_type = adafruit_max31856.ThermocoupleType.T)
Rthermocouple = adafruit_max31856.MAX31856(spi, Rcs, thermocouple_type = adafruit_max31856.ThermocoupleType.T)

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Configure the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
# backlight.value = True

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
absdir = os.path.dirname(os.path.realpath(__file__))
font = ImageFont.truetype(os.path.join(absdir, "DejaVuSans.ttf"), 24)


def _enumerateDevices():
    _filter = ''
    if platform.system() == "Darwin":
        _filter = 'usbmodem'
    if platform.system() == "Linux":
        _filter = 'ttyACM'
    _devs = ['/dev/serial0']
    for _dev in os.listdir('/dev'):
        if _filter.lower() in _dev.lower():
            _devs.append(_dev)
    return _devs


def main(stdscr):
    spinner = [('|', 250), ('\\', 251), ('—', 252), ('/', 253)]

    backlight.value = True
    start_time = time.time()
    curses.start_color()
    # use 250 to not interfere with tests later
    curses.init_color(250, 1000, 0, 0)
    curses.init_pair(250, 250, curses.COLOR_BLACK)
    curses.init_color(251, 0, 1000, 0)
    curses.init_pair(251, 251, curses.COLOR_BLACK)
    curses.init_color(252, 0, 0, 1000)
    curses.init_pair(252, 252, curses.COLOR_BLACK)
    curses.init_color(253, 1000, 0, 1000)
    curses.init_pair(253, 253, curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.clear()
    stdscr.nodelay(True)
    temp_win = curses.newwin(4, 36, 2, 0)
    temp_win.border()
    _i = 0
    try:
        while True:
            if time.time() - start_time < 1:
                GPIO.output(led, GPIO.HIGH)
            elif time.time() - start_time > 2:
                GPIO.output(led, GPIO.LOW)
                start_time = time.time()

            if _i == len(spinner):
                _i = 0
            stdscr.addstr(0, 0, f"{spinner[_i][0]}", curses.color_pair(spinner[_i][1]))
            stdscr.refresh()

            LT = f"Left: {thermothread.lefttemp:0.1f} °C"
            RT = f"Right: {thermothread.righttemp:0.1f} °C"
            _v = thermothread.voltage
            if abs(_v) < 0.01:
                V = f"Volt.: {_v*1000:0.4f} mV"
            else:
                V = f"Volt.: {_v:0.6f} V"
            temp_win.addstr(1, 3, LT, curses.A_BOLD)
            temp_win.addstr('  ')
            temp_win.addstr(RT, curses.A_BOLD)
            temp_win.addstr(2, 3, V, curses.A_BOLD)
            temp_win.refresh()
   

            _i += 1
            cmd = "hostname -I | cut -d' ' -f1"
            IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
            # Draw a black filled box to clear the image.
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            # Write four lines of text.
            y = top
            draw.text((x, y), IP, font=font, fill="#FFFFFF")
            y += font.getsize(IP)[1]
            draw.text((x, y), LT, font=font, fill="#FFFF00")
            y += font.getsize(LT)[1]
            draw.text((x, y), RT, font=font, fill="#00FF00")
            y += font.getsize(RT)[1]
            draw.text((x, y), V, font=font, fill="#0000FF")
            y += font.getsize(V)[1]

            # Display image.
            with thermothread.lock:
                disp.image(image, rotation)
                time.sleep(0.1)

            if stdscr.getch() in (113, 120):
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        temp_win.clear()
        stdscr.clear()


if __name__ == '__main__':
    alive = threading.Event()
    alive.set()
    for _dev in _enumerateDevices():
        voltmeter = K2182A(_dev)
        if voltmeter.initialize(auto_sense_range=True):
            break
        voltmeter = None
    thermothread = thermo(alive, {'left':Lthermocouple, 'right':Rthermocouple}, voltmeter, authkey=tc.AUTH_KEY)
    thermothread.start()
    curses.wrapper(main)
    print("\nKilling threads")
    thermothread.stop()
    alive.clear()
    time.sleep(1)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    disp.image(image, rotation)
    backlight.value = False
    GPIO.cleanup()
