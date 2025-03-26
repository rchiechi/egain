#!/bin/bash
~/bin/arduino-cli compile -b arduino:avr:uno --libraries ~/.arduino15/libraries/ --upload --port /dev/ttyACM0 ~/egain/thermo/arduino/peltier_LCD 
