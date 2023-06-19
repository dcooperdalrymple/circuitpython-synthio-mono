"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: voice.py
Title: Voice
Version: 0.1.0
Since: 0.1.0
"""

import time
import synthio
from rpi_pico_synthio.oscillator import Oscillator

class Voice:

    NUM_OSCILLATORS = 2

    FILTER_FREQUENCY_MAX = 20000.0
    FILTER_FREQUENCY_MIN = 20.0

    FILTER_RESONANCE_MAX = 2.0
    FILTER_RESONANCE_MIN = 0.7071067811865475

    def __init__(self, synth, patch):
        self.filterLfo = synthio.LFO()
        self.synth = synth
        self.oscillators = [Oscillator(i, self.synth) for i in range(self.NUM_OSCILLATORS)]

        self.active = False
        self.lastActive = -1
        self.lastFrequency = -1

        self.loadPatch(patch)

    def update(self):
        filterFrequency = min(max(self.patch.filterFrequency + self.filterLfo.value, 0.0), 1.0) * (self.FILTER_FREQUENCY_MAX - self.FILTER_FREQUENCY_MIN) + self.FILTER_FREQUENCY_MIN
        filterResonance = self.patch.filterResonance * (self.FILTER_RESONANCE_MAX - self.FILTER_RESONANCE_MIN) + self.FILTER_RESONANCE_MIN

        filter = None
        if self.patch.filterType == "lpf":
            filter = self.synth.low_pass_filter(filterFrequency, filterResonance)
        elif self.patch.filterType == "hpf":
            filter = self.synth.high_pass_filter(filterFrequency, filterResonance)
        elif self.patch.filterType == "bpf":
            filter = self.synth.band_pass_filter(filterFrequency, filterResonance)
        if not filter is None:
            for oscillator in self.oscillators:
                oscillator.setFilter(filter)

        for oscillator in self.oscillators:
            oscillator.update()

    def press(self, frequency, velocity):
        self.active = True
        self.lastActive = time.monotonic()
        self.lastFrequency = frequency
        for oscillator in self.oscillators:
            oscillator.press(frequency, velocity)

    def release(self):
        self.active = False
        for oscillator in self.oscillators:
            oscillator.release()

    def setBend(self, value):
        for oscillator in self.oscillators:
            oscillator.setBend(value)

    def loadPatch(self, patch):
        self.patch = patch
        self.patch.filterLfo.assign(self.filterLfo)
        for oscillator in self.oscillators:
            oscillator.loadPatch(patch)

    def isActive(self):
        return self.active
    def getLastActive(self):
        return self.lastActive
    def getLastFrequency(self):
        return self.lastFrequency

    def getSynth(self):
        return self.synth
