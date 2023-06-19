"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: patch.py
Title: Patch Settings
Version: 0.1.0
Since: 0.1.0
"""

import synthio

from rpi_pico_synthio.waveforms import Waveforms
from rpi_pico_synthio.voice import Voice

class Patch:

    def __init__(self):
        self.velocityAmount = 1.0
        self.bendAmount = 1.0

        self.amplitudeEnvelope = Envelope()

        self.filterType = "lpf"
        self.filterFrequency = 1.0
        self.filterResonance = 0.0
        self.filterLfo = LFO(depth=0.0, level=0.0)

        self.oscillators = [Oscillator() for i in range(Voice.NUM_OSCILLATORS)]
        for i in range(1, Voice.NUM_OSCILLATORS):
            self.oscillators[i].amplitudeLfo.level = 0.0

class Envelope:

    def __init__(self):
        self.envelope = synthio.Envelope(
            attack_time=0,
            decay_time=0.05,
            release_time=0,
            attack_level=1.0,
            sustain_level=0.75
        )

    def setAttackTime(self, value):
        self.envelope.attack_time = value
    def getAttackTime(self):
        return self.envelope.attack_time

    def setDecayTime(self, value):
        self.envelope.decay_time = value
    def getDecayTime(self):
        return self.envelope.decay_time

    def setReleaseTime(self, value):
        self.envelope.release_time = value
    def getReleaseTime(self):
        return self.envelope.release_time

    def setAttackLevel(self, value):
        self.envelope.attack_level = value
    def getAttackLevel(self):
        return self.envelope.attack_level

    def setSustainLevel(self, value):
        self.envelope.sustain_level = value
    def getSustainLevel(self):
        return self.envelope.sustain_level

    def get(self):
        return self.envelope

class LFO:

    def __init__(self, rate=1.0, depth=0.0, level=0.0):
        self.rate = rate
        self.depth = depth
        self.level = level
        self.lfo = None

    def setRate(self, value):
        self.rate = value
        if self.lfo:
            self.lfo.rate = self.rate
    def getRate(self):
        return self.rate

    def setDepth(self, value):
        self.depth = value
        if self.lfo:
            self.lfo.depth = self.depth
    def getDepth(self):
        return self.depth

    def setLevel(self, value):
        self.level = value
        if self.lfo:
            self.lfo.level = self.level
    def getLevel(self):
        return self.level

    def assign(self, lfo):
        self.lfo = lfo
        self.lfo.rate = self.rate
        self.lfo.scale = self.depth
        self.lfo.offset = self.level

class Oscillator:

    def __init__(self):
        self.oscillator = None
        self.waveform = list(Waveforms.keys())[0]
        self.coarseTune = 0.0
        self.fineTune = 0.0
        self.glide = 0.0
        self.amplitudeLfo = LFO(level=1.0)
        self.frequencyLfo = LFO()
        self.panningLfo = LFO()

    def setWaveform(self, waveform):
        self.waveform = waveform
        if self.oscillator:
            self.oscillator.setWaveform(self.waveform)
    def getWaveform(self):
        return self.waveform

    def setCoarseTune(self, value):
        self.coarseTune = value
    def getCoarseTune(self):
        return self.coarseTune

    def setFineTune(self, value):
        self.fineTune = value
    def getFineTune(self):
        return self.fineTune

    def setGlide(self, value):
        self.glide = value
        if self.oscillator:
            self.oscillator.setGlide(self.glide)
    def getGlide(self):
        return self.glide

    def assign(self, oscillator):
        self.oscillator = oscillator
        self.oscillator.setWaveform(self.getWaveform())
        self.oscillator.setGlide(self.getGlide())
        self.amplitudeLfo.assign(self.oscillator.amplitudeLfo)
        self.frequencyLfo.assign(self.oscillator.frequencyLfo)
        self.panningLfo.assign(self.oscillator.panningLfo)
