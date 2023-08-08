# circuitpython-synthio-mono: Basic Synthesizer Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import time, board, os
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

print("\n:: Initializing Audio ::")
audio = Audio(
    type=os.getenv("AUDIO_TYPE", "i2s"),
    i2s_clk=getenvgpio("AUDIO_CLK", "GP6"),
    i2s_ws=getenvgpio("AUDIO_WS", "GP7"),
    i2s_data=getenvgpio("AUDIO_DATA", "GP8"),
    pwm_left=getenvgpio("AUDIO_PWM_LEFT", "GP0"),
    pwm_right=getenvgpio("AUDIO_PWM_RIGHT", "GP1"),
    sample_rate=os.getenv("AUDIO_RATE", 22050),
    buffer_size=os.getenv("AUDIO_BUFFER", 4096)
)

print("\n:: Initializing Synthio ::")
synth = Synth(audio)

print("\n:: Building Waveforms ::")
waveforms = Waveforms(
    samples=os.getenv("WAVE_SAMPLES", 256),
    amplitude=os.getenv("WAVE_AMPLITUDE", 12000)
)

print("\n:: Building Voice ::")
min_filter_frequency=getenvfloat("OSC_FILTER_MIN_FREQ", 60.0)
max_filter_frequency=min(audio.get_sample_rate()*0.45, getenvfloat("OSC_FILTER_MAX_FREQ", 20000.0))
voice = Voice(
    synth,
    waveforms,
    min_filter_frequency=min_filter_frequency,
    max_filter_frequency=max_filter_frequency
)
voice.set_filter_resonance(0.25)
voice.set_filter_frequency(max_filter_frequency)
voice.set_pitch_bend_amount(1.0)
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
    uart=getenvbool("MIDI_UART", True),
    uart_tx=getenvgpio("MIDI_UART_TX", "GP4"),
    uart_rx=getenvgpio("MIDI_UART_RX", "GP5"),
    usb=getenvbool("MIDI_USB", False),
    ble=getenvbool("MIDI_BLE", False)
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
