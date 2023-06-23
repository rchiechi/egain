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


if __name__ == '__main__':
    spinner = ['|', '\\', '—', '/']
    alive = threading.Event()
    alive.set()
    for _dev in _enumerateDevices():
        voltmeter = K2182A(_dev)
        if voltmeter.initialize(auto_sense_range=True):
            break
        voltmeter = None
    thermothread = thermo(alive, {'left':Lthermocouple, 'right':Rthermocouple}, voltmeter, authkey=tc.AUTH_KEY)
    thermothread.start()
    backlight.value = True
    start_time = time.time()
    _i = 0
    try:
        while True:
            if time.time() - start_time < 1:
                GPIO.output(led, GPIO.HIGH)
            elif time.time() - start_time > 2:
                GPIO.output(led, GPIO.LOW)
                start_time = time.time()
            LT = f"Left:  {thermothread.lefttemp:0.1f} °C"
            RT = f"Right: {thermothread.righttemp:0.1f} °C"
            V = f"Voltage: {thermothread.voltage:0.6f} V"
            print(f"\r{LT}")
            print(RT)
            print(V)
            if _i == len(spinner):
                _i = 0
            print(f"{spinner[_i]}", end="\033[F\033[F\033[F")
            _i += 1
            V = "Voltage: 0.000 V"
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

    except KeyboardInterrupt:
        print("\nKilling threads")
        thermothread.stop()
        alive.clear()
        time.sleep(1)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        disp.image(image, rotation)
        backlight.value = False
        GPIO.cleanup()