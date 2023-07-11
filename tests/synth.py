# circuitpython-synthio-mono: Basic Synthesizer Test
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
print("circuitpython-synthio-mono: Basic Synthesizer Test")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/circuitpython-synthio-mono/")

gc.collect()

print("\n:: Reading Configuration ::")
config = Config()

print("\n:: Initializing Audio ::")
audio = Audio(
    type=config.get(("audio", "type"), "i2s"),
    i2s_clk=config.gpio(("audio", "clk"), "GP0"),
    i2s_ws=config.gpio(("audio", "ws"), "GP1"),
    i2s_data=config.gpio(("audio", "data"), "GP2"),
    pwm_left=config.gpio(("audio", "pwm_left"), "GP0"),
    pwm_right=config.gpio(("audio", "pwm_right"), "GP1"),
    sample_rate=config.get(("audio", "rate"), 22050),
    buffer_size=config.get(("audio", "buffer"), 4096)
)

print("\n:: Initializing Synthio ::")
synth = Synth(audio)

print("\n:: Building Waveforms ::")
waveforms = Waveforms(
    samples=config.get(("waveform", "samples"), 256),
    amplitude=config.get(("waveform", "amplitude"), 12000)
)

print("\n:: Building Voice ::")
min_filter_frequency=config.get(("oscillator", "filter", "min_frequency"), 60.0)
max_filter_frequency=min(audio.get_sample_rate()*0.45, config.get(("oscillator", "filter", "max_frequency"), 20000.0))
voice = Voice(
    synth,
    waveforms,
    min_filter_frequency=min_filter_frequency,
    max_filter_frequency=max_filter_frequency
)
voice.set_filter_resonance(0.25)
voice.set_filter_frequency(max_filter_frequency)
voice.oscillators[1].set_level(0.0)
voice.update()

print("\n:: Managing Keyboard ::")
keyboard = Keyboard()

def press(note, velocity):
    led.value = True
    voice.press(note, velocity)
keyboard.set_press(press)

def release():
    led.value = False
    voice.release()
keyboard.set_release(release)

print("\n:: Initializing Midi ::")
midi = Midi(
    uart_tx=config.gpio(("midi", "uart_tx"), "GP4"),
    uart_rx=config.gpio(("midi", "uart_rx"), "GP5")
)

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
midi.set_note_on(note_on)

def note_off(notenum):
    keyboard.remove(notenum)
midi.set_note_off(note_off)

def control_change(control, value):
    if control == 1:
        voice.set_filter_frequency(map_value(value, min_filter_frequency, max_filter_frequency))
    elif control == 7:
        audio.set_level(value)
    elif control == 64:
        keyboard.set_sustain(value)
midi.set_control_change(control_change)

def pitch_bend(value):
    voice.set_pitch_bend(value)
midi.set_pitch_bend(pitch_bend)

print("\n:: Watching Midi ::")
midi.init()
while True:
    voice.update()
    midi.update()
