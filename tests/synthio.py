# rpi-pico-synthio: Synthio Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time
import math
import board

from digitalio import DigitalInOut, Direction, Pull

from busio import UART
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.pitch_bend import PitchBend

from audiobusio import I2SOut
from audiomixer import Mixer

import synthio
import random
import ulab.numpy as numpy

# Program Constants

MIDI_CHANNEL        = 1
MIDI_THRU           = False
MIDI_TX             = board.GP4
MIDI_RX             = board.GP5

I2S_CLK             = board.GP0
I2S_WS              = board.GP1
I2S_DATA            = board.GP2

SAMPLE_RATE         = 22050
BUFFER_SIZE         = 4096

WAVE_SAMPLES        = 256
WAVE_AMPLITUDE      = 12000 # out of 16384

COARSE_TUNE_MAX     = 2.0
COARSE_TUNE_MIN     = 0.5

FINE_TUNE_MAX       = 1.0+1.0/12.0
FINE_TUNE_MIN       = 1.0-1.0/12.0/2

FILTER_FREQ_MAX     = min(SAMPLE_RATE*0.45, 20000)
FILTER_FREQ_MIN     = 60
FILTER_RES_MAX      = 16.0
FILTER_RES_MIN      = 0.25

ENVELOPE_TIME_MAX   = 2.0
ENVELOPE_TIME_MIN   = 0.05

BEND_AMOUNT_MAX     = 2.0
BEND_AMOUNT_MIN     = 1.0/12.0

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("rpi-pico-synthio: Synthio Test (Monophonic)")
print("Version 1.0")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/rpi-pico-synthio/")

print("\n:: Initializing Midi ::")

print("UART")
uart = UART(
    tx=MIDI_TX,
    rx=MIDI_RX,
    baudrate=31250,
    timeout=0.001
)

print("MIDI Controller")
midi = adafruit_midi.MIDI(
    midi_in=uart,
    midi_out=uart,
    in_channel=MIDI_CHANNEL-1,
    out_channel=MIDI_CHANNEL-1,
    debug=False
)
print("Channel:", midi.in_channel+1)

print("\n:: Initializing Audio ::")

print("I2S Audio Output")
audio = I2SOut(I2S_CLK, I2S_WS, I2S_DATA)

print("Audio Mixer")
mixer = Mixer(
    voice_count=1,
    sample_rate=SAMPLE_RATE,
    channel_count=2,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=BUFFER_SIZE
)
audio.play(mixer)

print("\n:: Initializing Synthio ::")

print("Building Waveforms")
waveforms = {
    "saw": numpy.linspace(WAVE_AMPLITUDE, -WAVE_AMPLITUDE, num=WAVE_SAMPLES, dtype=numpy.int16),
    "reverse_saw": numpy.array(numpy.flip(numpy.linspace(WAVE_AMPLITUDE, -WAVE_AMPLITUDE, num=WAVE_SAMPLES, dtype=numpy.int16)), dtype=numpy.int16),
    "square": numpy.concatenate((numpy.ones(WAVE_SAMPLES//2, dtype=numpy.int16)*WAVE_AMPLITUDE,numpy.ones(WAVE_SAMPLES//2, dtype=numpy.int16)*-WAVE_AMPLITUDE)),
    "sine": numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, WAVE_SAMPLES, endpoint=False)) * WAVE_AMPLITUDE, dtype=numpy.int16),
    "noise": numpy.array([random.randint(-WAVE_AMPLITUDE, WAVE_AMPLITUDE) for i in range(WAVE_SAMPLES)], dtype=numpy.int16)
}

print("Generating Synth")
synth = synthio.Synthesizer(
    sample_rate=SAMPLE_RATE,
    channel_count=2
)
mixer.voice[0].play(synth)

print("Building Voice")
filter_types = ["lpf", "hpf", "bpf"]

def map_value(value, min_value, max_value):
    return min(max((value * (max_value - min_value)) + min_value, min_value), max_value)
def map_value_centered(value, min_value, center_value, max_value):
    # TODO: Implement center threshold?
    if value > 0.5:
        return map_value((value - 0.5) * 2, center_value, max_value)
    elif value < 0.5:
        return map_value(value * 2, min_value, center_value)
    else:
        return center_value
def map_array(value, arr):
    index = math.floor(max(min(value * len(arr), len(arr) - 1), 0))
    return arr[index]
def map_dict(value, dict):
    return map_array(value, list(dict))

class Voice:
    def __init__(self):
        self.notenum = 0
        self.velocity = 0.0

        self.waveform = "saw"
        self._waveform = self.waveform
        self.coarse_tune = 0.5
        self.fine_tune = 0.5

        self.velocity_amount = 1.0
        self.attack_time = 0.0
        self.decay_time = 0.0
        self.release_time = 0.0
        self.attack_level = 1.0
        self.sustain_level = 0.75

        self.filter_type = "lpf"
        self._filter_type = self.filter_type
        self.filter_frequency = 1.0
        self.filter_resonance = 0.0

        self.bend = 0.0
        self.bend_amount = 0.0

        self.note = synthio.Note(
            waveform=self.get_waveform(),
            frequency=0.0,
            envelope=self.build_envelope(),
            amplitude=synthio.LFO( # Tremolo
                waveform=waveforms.get("sine", None),
                rate=1.0,
                scale=0.0,
                offset=1.0
            ),
            bend=synthio.LFO( # Vibrato
                waveform=waveforms.get("sine", None),
                rate=1.0,
                scale=0.0,
                offset=0.0
            ),
            panning=synthio.LFO( # Panning
                waveform=waveforms.get("sine", None),
                rate=1.0,
                scale=0.0,
                offset=0.0
            ),
            filter=self.build_filter()
        )
        synth.blocks.append(self.note.amplitude)
        synth.blocks.append(self.note.bend)
        synth.blocks.append(self.note.panning)

    def press(self, notenum, velocity):
        self.velocity = velocity
        self.update_envelope()
        if notenum != self.notenum:
            self.set_frequency(notenum)
            synth.press(self.note)
    def release(self):
        synth.release(self.note)
        self.notenum = 0

    def get_frequency(self, notenum=None):
        if not notenum:
            notenum = self.notenum
        return synthio.midi_to_hz(notenum) * map_value_centered(self.coarse_tune, COARSE_TUNE_MIN, 1.0, COARSE_TUNE_MAX) * map_value_centered(self.fine_tune, FINE_TUNE_MIN, 1.0, FINE_TUNE_MAX)
    def set_frequency(self, notenum=None):
        if notenum:
            self.notenum = notenum
        self.note.frequency = self.get_frequency()
    def set_coarse_tune(self, value, update=True):
        self.coarse_tune = value
        if update:
            self.set_frequency()
    def set_fine_tune(self, value, update=True):
        self.fine_tune = value
        if update:
            self.set_frequency()

    def get_velocity_mod(self):
        return 1.0 - (1.0 - self.velocity) * self.velocity_amount

    def set_waveform(self, value, update=True):
        self.waveform = map_dict(value, waveforms)
        if update and self.waveform != self._waveform:
            self._waveform = self.waveform
            self.note.waveform = self.get_waveform()
    def get_waveform(self):
        return waveforms.get(self.waveform, None)

    def build_filter(self):
        type = self.get_filter_type()
        if type == "lpf":
            return synth.low_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
        elif type == "hpf":
            return synth.high_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
        else: # "bpf"
            return synth.band_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
    def update_filter(self):
        self.note.filter = self.build_filter()
    def get_filter_type(self):
        return self.filter_type
    def set_filter_type(self, value, update=True):
        self.filter_type = map_array(value, filter_types)
        if update and self.filter_type != self._filter_type:
            self._filter_type = self.filter_type
            self.update_filter()
    def set_filter_frequency(self, value, update=True):
        self.filter_frequency = value
        if update:
            self.update_filter()
    def get_filter_frequency(self, map=True):
        if map:
            return map_value(self.filter_frequency, FILTER_FREQ_MIN, FILTER_FREQ_MAX)
        else:
            return self.filter_frequency
    def set_filter_resonance(self, value, update=True):
        self.filter_resonance = value
        if update:
            self.update_filter()
    def get_filter_resonance(self, map=True):
        if map:
            return map_value(self.filter_resonance, FILTER_RES_MIN, FILTER_RES_MAX)
        else:
            return self.filter_resonance

    def build_envelope(self):
        return synthio.Envelope(
            attack_time=map_value(self.attack_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX),
            decay_time=map_value(self.decay_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX),
            release_time=map_value(self.release_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX),
            attack_level=self.get_velocity_mod() * self.attack_level,
            sustain_level=self.get_velocity_mod() * self.sustain_level
        )
    def update_envelope(self):
        self.note.envelope = self.build_envelope()
    def set_envelope_attack_time(self, value, update=True):
        self.attack_time = value
        if update:
            self.update_envelope()
    def set_envelope_decay_time(self, value, update=True):
        self.decay_time = value
        if update:
            self.update_envelope()
    def set_envelope_release_time(self, value, update=True):
        self.release_time = value
        if update:
            self.update_envelope()
    def set_envelope_attack_level(self, value, update=True):
        self.attack_level = value
        if update:
            self.update_envelope()
    def set_envelope_sustain_level(self, value, update=True):
        self.sustain_level = value
        if update:
            self.update_envelope()

    def update_bend(self):
        self.note.bend.offset = self.bend * map_value(self.bend_amount, BEND_AMOUNT_MIN, BEND_AMOUNT_MAX)
    def set_bend(self, value, update=True):
        self.bend = value
        if update:
            self.update_bend()
    def set_bend_amount(self, value, update=True):
        self.bend_amount = value
        if update:
            self.update_bend()

voice = Voice()

print("Managing Keyboard")

note_types = ["high", "low", "last"]
class Keyboard:
    def __init__(self):
        self.notes = []
        self.type = note_types[0]

    def get_type(self):
        return self.type
    def set_type(self, value):
        self.type = map_array(value, note_types)

    def _get_low(self):
        if not self.notes:
            return None
        index = 0
        notenum = 127
        velocity = 1.0
        for i in range(len(self.notes)):
            if self.notes[i][0] < notenum:
                index = i
                notenum = self.notes[i][0]
                velocity = self.notes[i][1]
        return (index, notenum, velocity)
    def _get_high(self):
        if not self.notes:
            return None
        index = 0
        notenum = 0
        velocity = 1.0
        for i in range(len(self.notes)):
            if self.notes[i][0] > notenum:
                index = i
                notenum = self.notes[i][0]
                velocity = self.notes[i][1]
        return (index, notenum, velocity)
    def _get_last(self):
        if not self.notes:
            return None
        return (len(self.notes)-1, self.notes[len(self.notes)-1][0], self.notes[len(self.notes)-1][1])
    def get(self):
        if self.type == "high":
            return self._get_high()
        elif self.type == "low":
            return self._get_low()
        else: # "last"
            return self._get_last()

    def append(self, notenum, velocity, update=True):
        for i in range(len(self.notes)):
            if self.notes[i][0] == notenum:
                self.notes[i][1] = velocity
                return
        self.notes.append((notenum, velocity))
        if update:
            self.update()
    def remove(self, notenum, update=True):
        self.notes = [note for note in self.notes if note[0] != notenum]
        if update:
            self.update()

    def update(self):
        note = self.get()
        if not note:
            voice.release()
        else:
            voice.press(note[1], note[2])

keyboard = Keyboard()

print("\n:: Initialization Complete ::")

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
def note_off(notenum):
    keyboard.remove(notenum)

def control_change(control, value):
    if control == 7: # Volume
        mixer.voice[0].level = value

    elif control == 70: # Waveform
        voice.set_waveform(value)

    elif control == 12: # Tremolo Rate
        voice.note.amplitude.rate = value
    elif control == 92: # Tremolo Depth
        voice.note.amplitude.scale = value
    elif control == 13: # Tremolo Level Offset
        voice.note.amplitude.offset = value

    elif control == 76: # Vibrato Rate
        voice.note.bend.rate = value
    elif control == 77: # Vibrato Depth
        voice.note.bend.scale = value
    elif control == 78: # Pitch Bend Amount
        voice.set_bend_amount(value)

    elif control == 16: # Pan Rate
        voice.note.panning.rate = value
    elif control == 17: # Pan Depth
        voice.note.panning.scale = value
    elif control == 18: # Pan Offset
        voice.note.panning.offset = value

    elif control == 71: # Velocity Amount
        voice.velocity_amount = value
    elif control == 19: # Filter Type
        voice.set_filter_type(value)
    elif control == 80: # Filter Frequency
        voice.set_filter_frequency(value)
    elif control == 81: # Filter Resonance
        voice.set_filter_resonance(value)

    elif control == 73: # Envelope Attack Time
        voice.set_envelope_attack_time(value)
    elif control == 72: # Envelope Release Time
        voice.set_envelope_release_time(value)
    elif control == 82: # Envelope Decay Time
        voice.set_envelope_decay_time(value)
    elif control == 83: # Envelope Attack Level
        voice.set_envelope_attack_level(value)
    elif control == 79: # Envelope Sustain Level
        voice.set_envelope_sustain_level(value)

def pitch_bend(value):
    voice.set_bend(value)

while True:
    msg = midi.receive()
    if msg != None:
        if MIDI_THRU:
            midi.send(msg)
        if isinstance(msg, NoteOn):
            #print("Note On:", msg.note, msg.velocity / 127.0)
            if msg.velocity > 0.0:
                note_on(msg.note, msg.velocity / 127.0)
            else:
                note_off(msg.note)
        elif isinstance(msg, NoteOff):
            #print("Note Off:", msg.note)
            note_off(msg.note)
        elif isinstance(msg, ControlChange):
            #print("Control Change:", msg.control, msg.value / 127.0)
            control_change(msg.control, msg.value / 127.0)
        elif isinstance(msg, PitchBend):
            #print("Pitch Bend:", (msg.pitch_bend - 8192) / 8192)
            pitch_bend((msg.pitch_bend - 8192) / 8192);

print("\n:: Process Ended ::")
led.value = False