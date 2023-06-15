# rpi-pico-synthio: NeoTrellis Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time
import board

from digitalio import DigitalInOut, Direction, Pull
from busio import I2C
from adafruit_neotrellis.neotrellis import NeoTrellis

# Color Constants

COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 150, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_BLUE = (0, 0, 255)
COLOR_PURPLE = (180, 0, 255)
COLOR_GRAY = (150, 150, 150)
COLOR_WHITE = (255, 255, 255)

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("rpi-pico-synthio: NeoTrellis Test")
print("Version 1.0")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/rpi-pico-synthio/")

def handleTrellis(event):
    if event.edge == NeoTrellis.EDGE_RISING:
        trellis.pixels[event.number] = COLOR_CYAN
    elif event.edge == NeoTrellis.EDGE_FALLING:
        trellis.pixels[event.number] = COLOR_BLACK

# Initialize Controls (I2C, NeoTrellis, Display, & Rotary)
print("\n:: Initializing NeoTrellis ::")
trellis_i2c = I2C(scl=board.GP19, sda=board.GP18)

#trellis_interrupt = DigitalInOut(board.GP22)
#trellis_interrupt.direction = Direction.INPUT
#trellis_interrupt.pull = Pull.UP
trellis = NeoTrellis(trellis_i2c) #, interrupt=trellis_interrupt)
for i in range(16):
    trellis.pixels[i] = COLOR_BLACK
    time.sleep(0.05)

print("\n:: Activating Keys ::")
for i in range(16):
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    trellis.callbacks[i] = handleTrellis
    trellis.pixels[i] = COLOR_PURPLE
    time.sleep(0.05)
for i in range(16):
    trellis.pixels[i] = COLOR_BLACK
    time.sleep(0.05)

print("\n:: Watching Key Events ::")
while True:
    trellis.sync() # trigger callbacks
    time.sleep(0.02)

print("\n:: Complete ::")
led.value = False
