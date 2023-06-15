"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: audio.py
Title: Audio Output
Version: 0.1.0
Since: 0.1.0
"""

from audiopwmio import PWMAudioOut
from audiobusio import I2SOut
from audiomixer import Mixer

class Audio:

    def __init__(self):
        self.bufferSize = 256
        self.rate = 48000
        self.channels = 2
        self.bits = 16
        self.type = None
        self.volume = 1.0

    def initI2S(self, clk, ws, data):
        self.type = "i2s"
        self.driver = I2SOut(clk, ws, data)
        self.initMixer()

    def initPWM(self, left, right):
        self.type = "pwm"
        self.driver = PWMAudioOut(
            left_channel=left,
            right_channel=right
        )
        self.initMixer()

    def getType(self):
        return self.type

    def initMixer(self):
        if self.type is None:
            return
        self.mixer = Mixer(
            voice_count=1,
            sample_rate=self.rate,
            channel_count=self.channels,
            bits_per_sample=self.bits,
            samples_signed=True,
            buffer_size=self.bufferSize
        )
        self.driver.play(self.mixer)

    def attachSynth(self, synth):
        if self.type is None:
            return
        self.mixer.voice[0].play(synth.getVoice())

    def attachMidi(self, midi):
        # TODO: Control Event Volume, allow multiple events?
        pass
