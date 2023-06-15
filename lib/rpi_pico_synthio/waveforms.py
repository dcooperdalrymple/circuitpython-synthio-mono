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

class Waveforms:

    SAMPLES = 256
    AMPLITUDE = 12000 # out of 16384

    def __init__(self):
        self.waveforms = {
            "saw": numpy.linspace(self.AMPLITUDE, -self.AMPLITUDE, num=self.SAMPLES, dtype=numpy.int16),
            "square": numpy.concatenate((numpy.ones(self.SAMPLES//2, dtype=numpy.int16)*self.AMPLITUDE,numpy.ones(self.SAMPLES//2, dtype=numpy.int16)*-self.AMPLITUDE)),
            "sine": numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, self.SAMPLES, endpoint=False)) * self.AMPLITUDE, dtype=numpy.int16),
            "noise": numpy.array([random.randint(-self.AMPLITUDE, self.AMPLITUDE) for i in range(self.SAMPLES)], dtype=numpy.int16),
        }

    def get(self, name):
        waveform = self.waveforms.get(name, None)
        if waveform:
            return waveform
        return self.waveforms.get("saw", None)
