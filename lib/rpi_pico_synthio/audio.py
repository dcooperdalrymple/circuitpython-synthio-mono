"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: audio.py
Title: Audio Output
Version: 0.1.0
Since: 0.1.0
"""

from rpi_pico_synthio.lerp import Lerp

from audiopwmio import PWMAudioOut
from audiobusio import I2SOut
from audiomixer import Mixer

class Audio:

    def __init__(self, sampleRate=22050, bufferSize=256):
        self.type = None
        self.sampleRate = sampleRate
        self.bufferSize = bufferSize
        self.volume = Lerp(1.0, 1.0)

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

    def initMixer(self):
        if self.type is None:
            return
        self.mixer = Mixer(
            voice_count=1,
            sample_rate=self.sampleRate,
            channel_count=2,
            bits_per_sample=16,
            samples_signed=True,
            buffer_size=self.bufferSize
        )
        self.driver.play(self.mixer)

    def getType(self):
        return self.type

    def update(self):
        self.mixer.voice[0].level = self.volume.get(True)

    def attachSynth(self, synth):
        if self.type is None:
            return
        self.mixer.voice[0].play(synth.getSynth())

    def controlChange(self, control, value):
        if control == 7: # Volume
            self.volume.set(value)
    def attachMidi(self, midi):
        midi.addControlChangeEvent(self.controlChange)

    def menuUpdate(self, item):
        if item.get_key() == "volume":
            audio.setVolume(item.get() / 100.0)
    def attachMenu(self, menu):
        menu.addItemEvent(self.menuUpdate)

    def setVolume(self, value):
        value = min(max(value, 0.0), 1.0)
        self.volume.set(value)
