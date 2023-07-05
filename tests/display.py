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

print("\n:: Initializing Display ::")
display = get_display(config)
display.set_value("Display Test")
display.show_cursor(0, 0)

print("\n:: Running Test ::")
i = 0
while True:
    display.set_title(i)
    i = i + 1
    time.sleep(0.25)
