# rpi-pico-synthio: SSD1306 Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time
import board

from digitalio import DigitalInOut, Direction

from busio import I2C
import displayio
import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label

# Program Constants

DISPLAY_ADDRESS   = 0x3c
DISPLAY_WIDTH     = 128
DISPLAY_HEIGHT    = 64

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("rpi-pico-synthio: SSD1306 Display Test")
print("Version 1.0")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/rpi-pico-synthio/")

# Initialize Controls (I2C, NeoTrellis, Display, & Rotary)
print("\n:: Resetting Display and Initializing ::")
display_i2c = I2C(scl=board.GP21, sda=board.GP20)

displayio.release_displays()
display_bus = displayio.I2CDisplay(display_i2c, device_address=DISPLAY_ADDRESS)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

# Initialization Screen
print("\n:: Drawing Screen ::")
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

inner_bitmap = displayio.Bitmap(DISPLAY_WIDTH - 10, DISPLAY_HEIGHT - 8, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=5, y=4)
splash.append(inner_sprite)

text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=(DISPLAY_HEIGHT>>1)-1)
splash.append(text_area)

print("\n:: Complete ::")
displayio.release_displays()
led.value = False
