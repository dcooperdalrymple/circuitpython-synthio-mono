"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: oscillator.py
Title: Oscillator
Version: 0.1.0
Since: 0.1.0
"""

import synthio

from rpi_pico_synthio.lerp import Lerp
from rpi_pico_synthio.waveforms import Waveforms, LfoWaveform

class Oscillator:

    def __init__(self, index, synth):
        self.index = 0
        self.synth = synth
        self.patch = None

        self.amplitudeLfo = synthio.LFO(waveform=LfoWaveform)
        self.synth.blocks.append(self.amplitudeLfo)

        self.frequencyLfo = synthio.LFO(waveform=LfoWaveform)
        self.synth.blocks.append(self.frequencyLfo)

        self.panningLfo = synthio.LFO(waveform=LfoWaveform)
        self.synth.blocks.append(self.panningLfo)

        self.frequency = Lerp(0.0, 1.0) # Lerp Speed is Glide
        self.note = synthio.Note(
            frequency=self.frequency.get(),
            amplitude=self.amplitudeLfo,
            panning=self.panningLfo,
            bend=self.frequencyLfo
        )

    def loadPatch(self, patch):
        self.patch = patch
        self.note.envelope = self.patch.amplitudeEnvelope.get()
        self.patch.oscillators[self.index].assign(self)

    def update(self):
        self.note.frequency = max(min(self.frequency.get(True) * (1 + self.patch.oscillators[self.index].getCoarseTune() / 12) * (1 + self.patch.oscillators[self.index].getFineTune() / 12), 32767), 0)

    def setWaveform(self, waveform):
        if type(waveform) == type(""):
            waveform = Waveforms.get(waveform, None)
        self.note.waveform = waveform

    def setGlide(self, value):
        value = 1.0 - value
        self.frequency.setSpeed(value * value)

    def setFrequency(self, value):
        self.frequency.set(value)

    def setAmplitude(self, value):
        self.note.amplitude = value

    def setBend(self, value):
        self.note.bend = value * self.patch.bendAmount

    def setFilter(self, filter):
        self.note.filter = filter

    def press(self, frequency, velocity):
        self.setFrequency(frequency)
        self.setAmplitude(1.0 - (1.0 - velocity) * self.patch.velocityAmount)
        self.synth.press(self.note)

    def release(self):
        self.synth.release(self.note)
