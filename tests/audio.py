# circuitpython-synthio-mono: Audio Test
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
print("circuitpython-synthio-mono: Audio Test")
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

print("\n:: Testing Oscillator ::")
while True:
    led.value = True
    voice.press(60, 1.0)
    time.sleep(1)
    led.value = False
    voice.release()
    time.sleep(1)
