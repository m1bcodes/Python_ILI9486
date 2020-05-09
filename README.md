Python ILI9486
=======================

Python library to control an ILI9486 TFT LCD display.  Allows simple drawing on the display without installing a kernel module.

Designed specifically to work with the 3.5" LCD's  

For all platforms (Raspberry Pi) make sure you have the following dependencies:

````
sudo apt update
sudo apt upgrade -y
sudo apt install build-essential python3-dev python3-smbus python3-venv
sudo apt install libfreetype6-dev libjpeg-dev
````

## Installation and use

Create a virtualenv:

````
mkdir -p lcd
cd lcd
python3 -m venv .venv
source .venv/bin/activate
````

Install dependencies:

````
pip install wheel
pip install adafruit-gpio
pip install pillow
pip install numpy
pip install rpi.gpio
````

Install the library by downloading with the download link on the right, unzipping the archive, navigating inside the library's directory and executing:

````
sudo python setup.py install
````

See example of usage in the examples folder.

### Observation

SPI access must be done by a root user. So, if a Permission Error occurs, run the script as sudo:

````
sudo .venv/bin/python image.py
````


## Notes

Adafruit invests time and resources providing this open source code, please support Adafruit and open-source hardware by purchasing products from Adafruit!

Written by Tony DiCola for Adafruit Industries.

MIT license, all text above must be included in any redistribution
