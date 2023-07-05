# circuitpython-synthio-mono: Display Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import time, board
from digitalio import DigitalInOut, Direction
from synthio_mono import *

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("circuitpython-synthio-mono: Display Test")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/circuitpython-synthio-mono/")

gc.collect()

print("\n:: Reading Configuration ::")
config = Config()

print("\n:: Initializing Encoder ::")
encoder = Encoder(
    pin_a=config.gpio(("encoder", "a"), "GP11"),
    pin_b=config.gpio(("encoder", "b"), "GP12"),
    pin_button=config.gpio(("encoder", "btn"), "GP13")
)

def increment():
    print("Increment")
encoder.set_increment(increment)

def decrement():
    print("Decrement")
encoder.set_decrement(decrement)

def click():
    print("Click")
encoder.set_click(click)

def double_click():
    print("Double Click")
encoder.set_double_click(double_click)

def long_press():
    print("Long Press")
encoder.set_long_press(long_press)

print("\n:: Watching Encoder ::")
while True:
    encoder.update()
