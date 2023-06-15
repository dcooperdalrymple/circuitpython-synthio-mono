"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: synth.py
Title: Synth
Version: 0.1.0
Since: 0.1.0
"""

import synthio
from rpi_pico_synthio.waveforms import Waveforms
from rpi_pico_synthio.patch import Patch

class Synth:

    def __init__(self, sampleRate=48000, channels=2):
        self.synth = synthio.Synthesizer(
            sample_rate=sampleRate,
            channel_count=channels
        )
        self.notes = {}

        self.waveforms = Waveforms()

        # Load default patch
        self.loadPatch(Patch())

    def loadPatch(self, patch):
        self.patch = patch

    def getVoice(self):
        return self.synth

    def appendNote(self, frequency, velocity):
        notes = []
        notes.append(synthio.Note(
            frequency=frequency,
            amplitude=velocity,
            envelope=self.patch.amplitudeEnvelope.get(),
            waveform=self.waveforms.get(self.patch.waveform)
        ))
        self.notes[frequency] = notes
        self.synth.press(notes)

    def removeNote(self, frequency):
        notes = self.notes.get(frequency, None)
        if notes:
            self.synth.release(notes)
            del self.notes[frequency]

    def noteOn(self, note, velocity):
        self.appendNote(synthio.midi_to_hz(note), velocity)

    def noteOff(self, note):
        self.removeNote(synthio.midi_to_hz(note))

    def controlChange(self, control, value):
        if control == 1: # Mod Wheel
            pass
        elif control == 7: # Volume
            pass

    def pitchBend(self, value):
        for notes in self.notes.values():
            for n in notes:
                n.bend = value

    def attachMidi(self, midi):
        midi.noteOnEvent = self.noteOn
        midi.noteOffEvent = self.noteOff
        midi.controlChangeEvent = self.controlChange
        midi.pitchBendEvent = self.pitchBend
