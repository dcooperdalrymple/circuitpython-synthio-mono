# circuitpython-synthio-mono: MIDI Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import time, board
from digitalio import DigitalInOut, Direction, Pull
from synthio_mono import *

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("circuitpython-synthio-mono: MIDI Test")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/circuitpython-synthio-mono/")

gc.collect()

print("\n:: Reading Configuration ::")
config = Config()

print("\n:: Initializing Midi ::")
midi = Midi(
    uart_tx=config.gpio(("midi", "uart_tx"), "GP4"),
    uart_rx=config.gpio(("midi", "uart_rx"), "GP5")
)

def note_on(notenum, velocity):
    led.value = True
    print("Note On: {:d} {:02f}".format(notenum, velocity))
midi.set_note_on(note_on)

def note_off(notenum):
    led.value = False
    print("Note Off: {:d}".format(notenum))
midi.set_note_off(note_off)

def control_change(control, value):
    print("Control Change: {:d} {:02f}".format(control, value))
midi.set_control_change(control_change)

def pitch_bend(value):
    print("Pitch Bend: {:02f}".format(value))
midi.set_pitch_bend(pitch_bend)

def program_change(patch):
    print("Program Change: {:d}".format(patch))
midi.set_program_change(program_change)

print("\n:: Watching Midi ::")
midi.init()
while True:
    midi.update()
