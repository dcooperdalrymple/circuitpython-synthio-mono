"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: code.py
Title: Main Script
Version: 0.1.0
Since: 0.1.0
"""

import sys
import time
import board

from digitalio import DigitalInOut, Direction, Pull

from rpi_pico_synthio.neotrellis import NeoTrellis
from rpi_pico_synthio.menu import Menu
from rpi_pico_synthio.config import Config
from rpi_pico_synthio.audio import Audio
from rpi_pico_synthio.synth import Synth
from rpi_pico_synthio.midi import Midi

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Initialize NeoTrellis I2C RGB 4x4 Button Pad
neotrellis = NeoTrellis(
    scl=board.GP19,
    sda=board.GP18
)

# Initialize Menu Display and Encoder
menu = Menu(
    scl=board.GP21,
    sda=board.GP20,
    encoder_pin_a=board.GP12,
    encoder_pin_b=board.GP13,
    button_pin=board.GP7
)

# Initialization Screen
menu.splash_image()
menu.splash_message("Version 0.1.0")

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("rpi-pico-synthio\nVersion 0.1.0\nCooper Dalrymple, 2023\nhttps://dcdalrymple.com/rpi-pico-synthio/")

menu.splash_message("Reading Flash Memory")
print(":: Reading Flash Memory ::")
config = Config()
try:
    config.readFlashSettings()
except:
    print("No internal config file detected.")

menu.splash_message("Reading SD Card")
print(":: Reading SD Card ::")
try:
    config.initSD(board.GP10, board.GP11, board.GP8, board.GP9)
    config.readSDSettings()
except:
    print("No SD card detected or invalid file system format. SD card must be formatted as FAT32.")

menu.splash_message("Initializing Audio")
print(":: Initializing Audio ::")
audio = Audio(config.getAudioRate(), config.getAudioBufferSize())
if config.getAudioOutput() == "pwm":
    audio.initPWM(board.GP16, board.GP17)
elif config.getAudioOutput() == "i2s":
    audio.initI2S(board.GP0, board.GP1, board.GP2)
if audio.getType() == None:
    menu.splash_message("Invalid Audio Output")
    print("Invalid audio output type. Please see repository for valid output types.")
    sys.exit()

menu.splash_message("Initializing Synthio")
print(":: Initializing Synthio ::")
synth = Synth(config.getAudioRate())
audio.attachSynth(synth)

print("Buffer Size:", config.getAudioBufferSize())
print("Sample Rate:", config.getAudioRate())
print("Channels:", 2)
print("Bits:", 16)
print("Output:", config.getAudioOutput())

menu.splash_message("Initializing Midi")
print(":: Initializing Midi ::")
midi = Midi(board.GP4, board.GP5, config.getMidiChannel(), config.getMidiThru())
print("Channel:", midi.getChannel())
audio.attachMidi(midi)
synth.attachMidi(midi)

menu.splash_message("Initializing Interface")
print(":: Initializing Interface ::")

print("Activating NeoTrellis Keys")
synth.attachNeoTrellis(neotrellis)
neotrellis.activateAll(True)

print("Activating Display Menu")
audio.attachMenu(menu)
midi.attachMenu(menu)
synth.attachMenu(menu)

menu.splash_message("Initialization Complete")
print(":: Initialization Complete ::")
led.value = False

menu.setup()

while True:
    neotrellis.update()
    menu.update()
    midi.update()
    audio.update()
    synth.update()
    time.sleep(0.02)

print("\n:: Program Shutting Down ::")
menu.deinit()
