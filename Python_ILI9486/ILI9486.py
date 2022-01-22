# Copyright (c) 2016 myway work
# Author: Liqun Hu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import numbers
import time
import numpy as np
from enum import Enum

from PIL import Image, ImageDraw

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


# Constants for interacting with display registers.
ILI9486_TFTWIDTH    = 320
ILI9486_TFTHEIGHT   = 480

ILI9486_NOP         = 0x00
ILI9486_SWRESET     = 0x01
ILI9486_RDDID       = 0x04
ILI9486_RDDST       = 0x09

ILI9486_SLPIN       = 0x10
ILI9486_SLPOUT      = 0x11
ILI9486_PTLON       = 0x12
ILI9486_NORON       = 0x13

ILI9486_RDMODE      = 0x0A
ILI9486_RDMADCTL    = 0x0B
ILI9486_RDPIXFMT    = 0x0C
ILI9486_RDIMGFMT    = 0x0A
ILI9486_RDSELFDIAG  = 0x0F

ILI9486_INVOFF      = 0x20
ILI9486_INVON       = 0x21
ILI9486_GAMMASET    = 0x26
ILI9486_DISPOFF     = 0x28
ILI9486_DISPON      = 0x29

ILI9486_CASET       = 0x2A
ILI9486_PASET       = 0x2B
ILI9486_RAMWR       = 0x2C
ILI9486_RAMRD       = 0x2E

ILI9486_PTLAR       = 0x30
ILI9486_MADCTL      = 0x36
ILI9486_PIXFMT      = 0x3A

ILI9486_FRMCTR1     = 0xB1
ILI9486_FRMCTR2     = 0xB2
ILI9486_FRMCTR3     = 0xB3
ILI9486_INVCTR      = 0xB4
ILI9486_DFUNCTR     = 0xB6

ILI9486_PWCTR1      = 0xC0
ILI9486_PWCTR2      = 0xC1
ILI9486_PWCTR3      = 0xC2
ILI9486_PWCTR4      = 0xC3
ILI9486_PWCTR5      = 0xC4
ILI9486_VMCTR1      = 0xC5
ILI9486_VMCTR2      = 0xC7

ILI9486_RDID1       = 0xDA
ILI9486_RDID2       = 0xDB
ILI9486_RDID3       = 0xDC
ILI9486_RDID4       = 0xDD

ILI9486_GMCTRP1     = 0xE0
ILI9486_GMCTRN1     = 0xE1

ILI9486_PWCTR6      = 0xFC

ILI9486_BLACK       = 0x0000
ILI9486_BLUE        = 0x001F
ILI9486_RED         = 0xF800
ILI9486_GREEN       = 0x07E0
ILI9486_CYAN        = 0x07FF
ILI9486_MAGENTA     = 0xF81F
ILI9486_YELLOW      = 0xFFE0  
ILI9486_WHITE       = 0xFFFF

UpperLeft           = 0
UpperRight          = 1
LowerLeft           = 2
LowerRight          = 3

def color565(r, g, b):
    """Convert red, green, blue components to a 16-bit 565 RGB value. Components
    should be values 0 to 255.
    """
    return ((r & 0xF0) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def image_to_data(image):
    """Generator function to convert a PIL image to 16-bit 565 RGB bytes."""
    #NumPy is much faster at doing this. NumPy code provided by:
    #Keith (https://www.blogger.com/profile/02555547344016007163)
    pb = np.array(image.convert('RGB')).astype('uint16')
#    color = ((pb[:,:,0] & 0xF8) << 8) | ((pb[:,:,1] & 0xFC) << 3) | (pb[:,:,2] >> 3)
#    return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()
    return np.dstack((pb[:,:,0] & 0xFC, pb[:,:,1] & 0xFC, pb[:,:,2] & 0xFC)).flatten().tolist()
#    pixels = image.convert('RGB').load()  
#    width, height = image.size  
#    for y in range(height):  
#        for x in range(width):  
#            r,g,b = pixels[(x,y)]  
##            color = color565(r, g, b)  
#            #yield (color >> 8) & 0xFF  
#            #yield color & 0xFF  
#            yield r 
#            yield g  
#            yield b 
#

# Define a function to hard code that we are using a raspberry pi
def get_platform_gpio_for_pi(**keywords):
    import RPi.GPIO
    return GPIO.RPiGPIOAdapter(RPi.GPIO, **keywords)

class ILI9486(object):
    """Representation of an ILI9486 TFT LCD."""

    def __init__(self, dc, spi, rst=None, gpio=None, origin = UpperLeft, width=ILI9486_TFTWIDTH,
        height=ILI9486_TFTHEIGHT):
        """Create an instance of the display using SPI communication.  Must
        provide the GPIO pin number for the D/C pin and the SPI driver.  Can
        optionally provide the GPIO pin number for the reset pin as the rst
        parameter.
        """
        self._dc = dc
        self._rst = rst
        self._spi = spi
        self._gpio = gpio
        self.width = width
        self.height = height
        self.origin = origin

        if self._gpio is None:
            #self._gpio = GPIO.get_platform_gpio()
            self._gpio = get_platform_gpio_for_pi()
        # Set DC as output.
        self._gpio.setup(dc, GPIO.OUT)
        # Setup reset as output (if provided).
        if rst is not None:
            self._gpio.setup(rst, GPIO.OUT)
        # Set SPI to mode 0, MSB first.
        spi.set_mode(2)
        spi.set_bit_order(SPI.MSBFIRST)
        spi.set_clock_hz(64000000)
        # Create an image buffer.

    def send(self, data, is_data=True, chunk_size=4096):
        """Write a byte or array of bytes to the display. Is_data parameter
        controls if byte should be interpreted as display data (True) or command
        data (False).  Chunk_size is an optional size of bytes to write in a
        single SPI transaction, with a default of 4096.
        """
        # Set DC low for command, high for data.
        self._gpio.output(self._dc, is_data)
        # Convert scalar argument to list so either can be passed as parameter.
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        # Write data a chunk at a time.
        for start in range(0, len(data), chunk_size):
            end = min(start+chunk_size, len(data))
            self._spi.write(data[start:end])

    def command(self, data):
        """Write a byte or array of bytes to the display as command data."""
        self.send(data, False)

    def data(self, data):
        """Write a byte or array of bytes to the display as display data."""
        self.send(data, True)

    def swreset(self):
        self.command(ILI9486_SWRESET)

    def reset(self):
        """Reset the display, if reset pin is connected."""
        if self._rst is not None:
            self._gpio.set_high(self._rst)
            time.sleep(0.005)
            self._gpio.set_low(self._rst)
            time.sleep(0.02)
            self._gpio.set_high(self._rst)
            time.sleep(0.150)

    def _init(self):
        # Initialize the display.  Broken out as a separate function so it can
        # be overridden by other displays in the future.

        self.swreset()

        self.command(0xB0)  # Interface mode
        self.data(0x00)

        self.command(ILI9486_SLPOUT)
        time.sleep(0.020)
    
        self.command(ILI9486_PIXFMT)
        self.data(0x66)     # set 18bpp

        # self.command(ILI9486_RDPIXFMT)
        # self.data(0x66)

        # self.command(ILI9486_DFUNCTR)     # configuration from arduino shield
        # self.data(0x00)
        # self.data(0x42)
        # self.data(0x3B)

        # self.command(ILI9486_PWCTR1)
        # self.data(0x19)
        # self.data(0x1a)

        # self.command(ILI9486_PWCTR2)
        # self.data(0x45)
        # self.data(0x00)

        self.command(ILI9486_PWCTR3)        # power control for normal mode
        self.data(0x44)                     # 

        self.command(ILI9486_VMCTR1)
        self.data(0x00)
        self.data(0x00)
        self.data(0x00)
        self.data(0x00)
        
        self.command(ILI9486_INVON)     # we need inverion on to have the right colors

        # gamma = [0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00]
        pos_gamma = [0x1f, 0x25,0x22,0x0b,0x06,0x0a,0x4e,0xc6,0x39,0x00,0x00,0x00,0x00,0x00,0x00]
        # gamma = [128] * 15
        self.set_pos_gamma(pos_gamma)
        neg_gamma = [0x1f,0x3f,0x3f,0x0f,0x1f,0x0f,0x46,0x49,0x31,0x05,0x09,0x03,0x1c,0x1a,0x00]
        self.set_neg_gamma(neg_gamma)
        
        # gamma = gamma + [0x00]
        # gamma=[255] * 8 + [0] * 8
        # self.set_dig_gamma(gamma)     # seems to have no effect
            
        self.command(0x36)              # memory access control 
        if self.origin==UpperLeft:
            self.data(0b00101000)
            self.width,self.height = self.height, self.width
            pass
        elif self.origin==UpperRight:
            self.data(0x88) # b10001000                 # change coordinate system orientation etc. (NOte: No change on color scheme)
            pass
        elif self.origin==LowerLeft:
            self.data(0x48) # b01001000
            pass
        elif self.origin==LowerRight:
            self.data(0xE8) # b11101000
            self.width,self.height = self.height, self.width
            pass
        else:
            raise Exception("Unknown origin: %1" % self.origin)

        self.buffer = Image.new('RGB', (self.width, self.height))


        self.command(ILI9486_SLPOUT)
        self.command(ILI9486_DISPON)

    def begin(self):
        """Initialize the display.  Should be called once before other calls that
        interact with the display are called.
        """
        self.reset()
        self._init()    
    
    def set_pos_gamma(self, values):
        if len(values) != 15:
            raise Exception("Argument values must have 15 elements")
        self.command(ILI9486_GMCTRP1)
        for v in values:
            self.data(v)

    def set_neg_gamma(self, values):
        if len(values) != 15:
            raise Exception("Argument values must have 15 elements")
        self.command(ILI9486_GMCTRN1)
        for v in values:
            self.data(v)

    def set_dig_gamma(self, values):
        if len(values) != 16:
            raise Exception("Argument values must have 15 elements")
        self.command(0xE2)
        for v in values:
            self.data(v)

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        """Set the pixel address window for proceeding drawing commands. x0 and
        x1 should define the minimum and maximum x pixel bounds.  y0 and y1 
        should define the minimum and maximum y pixel bound.  If no parameters 
        are specified the default will be to update the entire display from 0,0
        to 239,319.
        """
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.command(0x2A)        # Column addr set
        self.data(x0 >> 8)
        self.data(x0 & 0xFF)                    # XSTART 
        self.data(x1 >> 8)
        self.data(x1 & 0xFF)                    # XEND
        self.command(0x2B)        # Row addr set
        self.data(y0 >> 8)
        self.data(y0 & 0xFF)                    # YSTART
        self.data(y1 >> 8)
        self.data(y1 & 0xFF)                    # YEND
        self.command(0x2C)        # write to RAM

    def display(self, image=None, rect=None):
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # By default write the internal buffer to the display.
        if image is None:
            image = self.buffer
            # Set address bounds to entire display.
            self.set_window()
        else:
            if rect is None:
                raise Exception("Expecting rect parameter")
            self.set_window(rect[0], rect[1], rect[2], rect[3])

        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(image_to_data(image))
        # Write data to hardware.
        self.data(pixelbytes)

    def clear(self, color=(0,0,0)):
        """Clear the image buffer to the specified RGB color (default black)."""
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

    def draw(self):
        """Return a PIL ImageDraw instance for 2D drawing on the image buffer."""
        return ImageDraw.Draw(self.buffer)
