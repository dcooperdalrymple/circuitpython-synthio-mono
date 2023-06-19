"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: waveforms.py
Title: Waveforms
Version: 0.1.0
Since: 0.1.0
"""

import random
import ulab.numpy as numpy

SAMPLES = 256
AMPLITUDE = 12000 # out of 16384

Waveforms = {
    "saw": numpy.linspace(AMPLITUDE, -AMPLITUDE, num=SAMPLES, dtype=numpy.int16),
    "reverse_saw": numpy.flip(numpy.linspace(AMPLITUDE, -AMPLITUDE, num=SAMPLES, dtype=numpy.int16)),
    "square": numpy.concatenate((numpy.ones(SAMPLES//2, dtype=numpy.int16)*AMPLITUDE,numpy.ones(SAMPLES//2, dtype=numpy.int16)*-AMPLITUDE)),
    "sine": numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, SAMPLES, endpoint=False)) * AMPLITUDE, dtype=numpy.int16),
    "noise": numpy.array([random.randint(-AMPLITUDE, AMPLITUDE) for i in range(SAMPLES)], dtype=numpy.int16),
}

LfoWaveform = Waveforms.get("sine")
