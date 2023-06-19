"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: synth.py
Title: Synth
Version: 0.1.0
Since: 0.1.0
"""

import math
import synthio
from rpi_pico_synthio.lerp import Lerp
from rpi_pico_synthio.patch import Patch
from rpi_pico_synthio.oscillator import Oscillator
from rpi_pico_synthio.voice import Voice
from rpi_pico_synthio.audio import Audio

class Synth:

    def __init__(self, sampleRate=22050):
        self.patch = Patch()

        self.synth = synthio.Synthesizer(
            sample_rate=sampleRate,
            channel_count=2
        )

        self.maxVoices = int(math.floor(self.synth.max_polyphony / Voice.NUM_OSCILLATORS))
        self.voices = [Voice(self.synth, self.patch) for i in range(self.maxVoices)]

        self.mod = Lerp(0.0, 1.0)
        self.bend = Lerp(0.0, 1.0)

    def getSynth(self):
        return self.synth

    def getPatch(self):
        return self.patch

    def getNextVoice(self):
        for voice in self.voices:
            if not voice.isActive():
                return voice

        index = 0
        lastActive = self.voices[0].getLastActive()
        for i in range(1, self.maxVoices):
            if self.voices[i].getLastActive() < lastActive:
                index = i
                lastActive = self.voices[i].getLastActive()
        return self.voices[index]

    def press(self, frequency, velocity):
        voice = self.getNextVoice()
        voice.press(frequency, velocity)

    def release(self, frequency):
        for voice in self.voices:
            if voice.getLastFrequency() == frequency:
                voice.release()
                return True
        return False

    def update(self):
        self.mod.update()
        self.bend.update()

        for voice in self.voices:
            voice.setBend(self.bend.get())
            voice.update()

    def loadPatch(self, patch):
        self.patch = patch
        for voice in self.voices:
            voice.loadPatch(patch)

    def noteOn(self, note, velocity):
        self.press(synthio.midi_to_hz(note), velocity)

    def noteOff(self, note):
        self.release(synthio.midi_to_hz(note))

    def controlChange(self, control, value):
        if control == 1: # Mod Wheel
            self.mod.set(value)

    def pitchBend(self, value):
        self.bend.set(value)

    def attachMidi(self, midi):
        midi.addNoteOnEvent(self.noteOn)
        midi.addNoteOffEvent(self.noteOff)
        midi.addControlChangeEvent(self.controlChange)
        midi.addPitchBendEvent(self.pitchBend)

    def attachNeoTrellis(self, neotrellis):
        neotrellis.addNoteOnEvent(self.noteOn)
        neotrellis.addNoteOffEvent(self.noteOff)

    def menuUpdate(self, item):
        if not self.patch:
            return

        key = item.get_key()
        print(key)

        if key == "velocity_amount":
            self.patch.velocityAmount = item.get()
        elif key == "bend_amount":
            self.patch.bendAmount = item.get()

        elif key == "amplitude_envelope_attack_time":
            self.patch.amplitudeEnvelope.setAttackTime(item.get())
        elif key == "amplitude_envelope_decay_time":
            self.patch.amplitudeEnvelope.setDecayTime(item.get())
        elif key == "amplitude_envelope_release_time":
            self.patch.amplitudeEnvelope.setReleaseTime(item.get())
        elif key == "amplitude_envelope_attack_level":
            self.patch.amplitudeEnvelope.setAttackLevel(item.get())
        elif key == "amplitude_envelope_sustain_level":
            self.patch.amplitudeEnvelope.setSustainLevel(item.get())
        elif key == "filter_type":
            self.patch.filterType = item.get()
        elif key == "filter_frequency":
            self.patch.filterFrequency = item.get()
        elif key == "filter_resonance":
            self.patch.filterResonance = item.get()
        elif key == "filter_lfo_rate":
            self.patch.filterLfo.setRate(item.get())
        elif key == "filter_lfo_depth":
            self.patch.filterLfo.setDeptch(item.get())
        elif key == "filter_lfo_level":
            self.patch.filterLfo.setLevel(item.get())

        elif key == "osc0_waveform":
            self.patch.oscillators[0].waveform = item.get()
        elif key == "osc0_coarse_tune":
            self.patch.oscillators[0].coarseTune = item.get()
        elif key == "osc0_fine_tune":
            self.patch.oscillators[0].fineTune = item.get()
        elif key == "osc0_glide":
            self.patch.oscillators[0].glide = item.get()
        elif key == "osc0_amplitude_lfo_rate":
            self.patch.oscillators[0].amplitudeLfo.setRate(item.get())
        elif key == "osc0_amplitude_lfo_depth":
            self.patch.oscillators[0].amplitudeLfo.setDepth(item.get())
        elif key == "osc0_amplitude_lfo_level":
            self.patch.oscillators[0].amplitudeLfo.setLevel(item.get())
        elif key == "osc0_frequency_lfo_rate":
            self.patch.oscillators[0].frequencyLfo.setRate(item.get())
        elif key == "osc0_frequency_lfo_depth":
            self.patch.oscillators[0].frequencyLfo.setDepth(item.get())
        elif key == "osc0_frequency_lfo_level":
            self.patch.oscillators[0].frequencyLfo.setLevel(item.get())
        elif key == "osc0_panning_lfo_rate":
            self.patch.oscillators[0].panningLfo.setRate(item.get())
        elif key == "osc0_panning_lfo_depth":
            self.patch.oscillators[0].panningLfo.setDepth(item.get())
        elif key == "osc0_panning_lfo_level":
            self.patch.oscillators[0].panningLfo.setLevel(item.get())

        elif key == "osc1_waveform":
            self.patch.oscillators[1].waveform = item.get()
        elif key == "osc1_coarse_tune":
            self.patch.oscillators[1].coarseTune = item.get()
        elif key == "osc1_fine_tune":
            self.patch.oscillators[1].fineTune = item.get()
        elif key == "osc1_glide":
            self.patch.oscillators[1].glide = item.get()
        elif key == "osc1_amplitude_lfo_rate":
            self.patch.oscillators[1].amplitudeLfo.setRate(item.get())
        elif key == "osc1_amplitude_lfo_depth":
            self.patch.oscillators[1].amplitudeLfo.setDepth(item.get())
        elif key == "osc1_amplitude_lfo_level":
            self.patch.oscillators[1].amplitudeLfo.setLevel(item.get())
        elif key == "osc1_frequency_lfo_rate":
            self.patch.oscillators[1].frequencyLfo.setRate(item.get())
        elif key == "osc1_frequency_lfo_depth":
            self.patch.oscillators[1].frequencyLfo.setDepth(item.get())
        elif key == "osc1_frequency_lfo_level":
            self.patch.oscillators[1].frequencyLfo.setLevel(item.get())
        elif key == "osc1_panning_lfo_rate":
            self.patch.oscillators[1].panningLfo.setRate(item.get())
        elif key == "osc1_panning_lfo_depth":
            self.patch.oscillators[1].panningLfo.setDepth(item.get())
        elif key == "osc1_panning_lfo_level":
            self.patch.oscillators[1].panningLfo.setLevel(item.get())

    def attachMenu(self, menu):
        menu.addItemEvent(self.menuUpdate)
