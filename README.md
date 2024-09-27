# EGaIn: Software to control and measure molecular junctions

This is the software we use in [our lab](https://www.rcclab.com) to measure the J/V properties of molecular junctions. It supports serial communication with a [Keithley Model 6430 Sub-Femtoamp Remote SourceMeter](https://www.tek.com/en/low-level-sensitive-and-specialty-instruments/high-resistance-low-current-electrometers-series-650-8). We use an [RS-232 to USB](https://iotmart.advantech.com/s/product/bb232usb9m/01t1W000009hiA5QAI) adapter. Data are written to text files formatted for ingestion by our [GaussFit](https://github.com/rchiechi/GaussFit) software.

The "EGaIn setup" consists of a syringe full of eutectic Ga-In suspended over a substrate. Tips and junctions can be formed manually or through software by entering the IP address of a [Newport ESP302 3-Axis controller](https://www.newport.com/f/esp30x-3-axis-dc-and-stepper-motion-controller) that is connected to the measurement stage. thermoelectric measurements can be performed using an Arduino device flashed with the [peltier.ino](https://github.com/rchiechi/egain/tree/main/thermo/arduino/peltier) file. The Arduino uses [Adafruit MAX31855](https://www.adafruit.com/product/269) thermocouples to measure temperature and a standard 12 V peltier plate to apply thermal gradients. Temperature control is achieved with a MOSFET on the negative terminal and the direction by two DPDT switches, all controlled by pins on the Arduino. We will eventually include schematics as well.

## Important

This software uses RS-232, not GPIB. Follow these steps to set the electrometer to RS-232 mode:
1. Press `MENU`
2. Navigate to `COMMUNICATION` and then press `ENTER`
3. Select `RS-232` and press `ENTER` (the electrometer needs to reboot for this setting to take effect)
