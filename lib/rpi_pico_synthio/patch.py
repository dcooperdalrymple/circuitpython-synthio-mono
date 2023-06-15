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

class Envelope:
    def __init__(self):
        self.attackTime = 0
        self.decayTime = 0.05
        self.releaseTime = 0
        self.attackLevel = 1.0
        self.sustainLevel = 0.75
    def get(self):
        return synthio.Envelope(
            attack_time=self.attackTime,
            decay_time=self.decayTime,
            release_time=self.releaseTime,
            attack_level=self.attackLevel,
            sustain_level=self.sustainLevel
        )

class Patch:
    def __init__(self):
        self.waveform = "saw"
        self.filterEnvelope = Envelope()
        self.amplitudeEnvelope = Envelope()
