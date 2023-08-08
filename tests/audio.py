# circuitpython-synthio-mono: Audio Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import time, board, os
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

print("\n:: Initializing Audio ::")
audio = Audio(
    type=os.getenv("AUDIO_TYPE","i2s"),
    i2s_clk=getenvgpio("AUDIO_CLK","GP0"),
    i2s_ws=getenvgpio("AUDIO_WS","GP1"),
    i2s_data=getenvgpio("AUDIO_DATA","GP2"),
    pwm_left=getenvgpio("AUDIO_PWM_LEFT","GP0"),
    pwm_right=getenvgpio("AUDIO_PWM_RIGHT","GP1"),
    sample_rate=os.getenv("AUDIO_RATE",22050),
    buffer_size=os.getenv("AUDIO_BUFFER",4096)
)

print("\n:: Initializing Synthio ::")
synth = Synth(audio)

print("\n:: Building Waveforms ::")
waveforms = Waveforms(
    samples=os.getenv("WAVE_SAMPLES",256),
    amplitude=os.getenv("WAVE_AMPLITUDE",12000)
)

print("\n:: Building Voice ::")
min_filter_frequency=getenvfloat("OSC_FILTER_MIN_FREQ",120.0,0)
max_filter_frequency=min(audio.get_sample_rate()*0.45, getenvfloat("OSC_FILTER_MAX_FREQ",20000.0,0))
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
