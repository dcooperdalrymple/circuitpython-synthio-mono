# rpi-pico-synthio: Synthio Test
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time
import math
import board

from digitalio import DigitalInOut, Direction, Pull

import json
import storage

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

MIDI_CHANNEL_MAX    = 16
MIDI_CHANNEL_MIN    = 1
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
    in_channel=0,
    out_channel=0,
    debug=False
)
print("Channel:", midi.in_channel+1)

print("\n:: Initializing Audio ::")

print("I2S Audio Output")
audio = I2SOut(I2S_CLK, I2S_WS, I2S_DATA)

print("Audio Mixer")
midi_thru = False
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
def map_boolean(value):
    if type(value) == type(False):
        return value
    else:
        return value >= 0.5
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
            self.update_waveform()
    def update_waveform(self):
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

voices = [Voice(), Voice()]

print("Managing Keyboard")

note_types = ["high", "low", "last"]
class Keyboard:
    def __init__(self):
        self.notes = []
        self.type = note_types[0]
        self.sustain = False
        self.sustained = []

    def get_type(self):
        return self.type
    def set_type(self, value):
        self.type = map_array(value, note_types)

    def get_sustain(self):
        return self.sustain
    def set_sustain(self, value, update=True):
        value = map_boolean(value)
        if value != self.sustain:
            self.sustain = val
            self.sustained = []
            if self.sustain:
                self.sustained = self.notes.view() # shallow copy
            if update:
                self.update()

    def _has_notes(self):
        if self.sustain and self.sustained:
            return True
        if self.notes
            return True
        return False
    def _get_low(self):
        if not self._has_notes():
            return None
        selected = (127, 0)
        if self.notes:
            for note in self.notes:
                if note[0] < selected[0]:
                    selected = note
        if self.sustain and self.sustained:
            for note in self.sustained:
                if note[0] < notenum:
                    selected = note
        return note
    def _get_high(self):
        if not self._has_notes():
            return None
        selected = (0, 0)
        for note in self.notes:
            if note[0] > selected[0]:
                selected = note
        return note
    def _get_last(self):
        if self.sustain and self.sustained:
            return self.sustained[-1]
        if self.notes:
            return self.notes[-1]
        return None
    def get(self):
        if self.type == "high":
            return self._get_high()
        elif self.type == "low":
            return self._get_low()
        else: # "last"
            return self._get_last()

    def append(self, notenum, velocity, update=True):
        self.remove(notenum, False, True)
        note = (notenum, velocity)
        self.notes.append(note)
        if self.sustain:
            self.sustained.append(note)
        if update:
            self.update()
    def remove(self, notenum, update=True, remove_sustained=False):
        self.notes = [note for note in self.notes if note[0] != notenum]
        if remove_sustained and self.sustain and self.sustained:
            self.sustained = [note for note in self.sustained if note[0] != notenum]
        if update:
            self.update()

    def update(self):
        note = self.get()
        if not note:
            for voice in voices:
                voice.release()
        else:
            for voice in voices:
                voice.press(note[0], note[1])

keyboard = Keyboard()

print("\n:: Initialization Complete ::")

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
def note_off(notenum):
    keyboard.remove(notenum)

parameters = [
    "midi_channel",
    "midi_thru",

    "volume",
    "portamento",
    "keyboard_type",
    "velocity_amount",
    "bend_amount",
    "filter_type",
    "filter_frequency",
    "filter_resonance",
    "pan",
    "attack_time",
    "decay_time",
    "release_time",
    "attack_level",
    "sustain_level",

    "portamento_0",
    "bend_amount_0",
    "waveform_0",
    "level_0",
    "coarse_tune_0",
    "fine_tune_0",
    "tremolo_rate_0",
    "tremolo_depth_0",
    "vibrato_rate_0",
    "vibrato_depth_0",
    "pan_rate_0",
    "pan_depth_0",
    "pan_0",

    "portamento_1",
    "bend_amount_1",
    "waveform_1",
    "level_1",
    "coarse_tune_1",
    "fine_tune_1",
    "tremolo_rate_1",
    "tremolo_depth_1",
    "vibrato_rate_1",
    "vibrato_depth_1",
    "pan_rate_1",
    "pan_depth_1",
    "pan_1",
]

cc_map = {
    7: "volume",
    5: "portamento",
    9: "keyboard_type",
    11: "velocity_amount",
    14: "bend_amount",
    15: "filter_type",
    12: "filter_frequency",
    13: "filter_resonance",
    10: "pan",
    16: "attack_time",
    17: "decay_time",
    18: "release_time",
    19: "attack_level",
    20: "sustain_level",

    21: "portamento_0",
    22: "bend_amount_0",
    23: "waveform_0",
    24: "level_0",
    25: "coarse_tune_0",
    26: "fine_tune_0",
    27: "tremolo_rate_0",
    28: "tremolo_depth_0",
    29: "vibrato_rate_0",
    30: "vibrato_depth_0",
    31: "pan_rate_0",
    70: "pan_depth_0",
    71: "pan_0",

    72: "portamento_1",
    73: "bend_amount_1",
    74: "waveform_1",
    75: "level_1",
    76: "coarse_tune_1",
    77: "fine_tune_1",
    78: "tremolo_rate_1",
    79: "tremolo_depth_1",
    80: "vibrato_rate_1",
    81: "vibrato_depth_1",
    82: "pan_rate_1",
    83: "pan_depth_1",
    84: "pan_1",

    85: "mod_parameter",
}
cc_mod = list(parameters)[0]

def set_parameter(name, value, update=True):
    if not name in parameters:
        return

    index = name[-1]
    if index.isdigit():
        index = int(index)
        name = name[:len(name)-2]
        if index >= len(voices):
            return
    else:
        index = None

    param_voices = None
    if index:
        param_voices = [voice[index]]
    else:
        param_voices = voices

    if name == "midi_channel":
        value = map_value(value, MIDI_CHANNEL_MIN, MIDI_CHANNEL_MAX)
        midi.in_channel = value
        midi.out_channel = value
    elif name == "midi_thru":
        midi_thru = map_boolean(value)

    elif name == "volume":
        mixer.voice[0].level = value
    elif name == "portamento":
        pass
    elif name == "keyboard_type":
        keyboard.set_type(value)
    elif name == "velocity_amount":
        for voice in param_voices:
            voice.velocity_amount = value
    elif name == "bend_amount":
        for voice in param_voices:
            voice.set_bend_amount(value, update)
    elif name == "mod_parameter":
        cc_mod = map_array(value, parameters)

    # TODO: Global filter
    elif name == "filter_type":
        for voice in param_voices:
            voice.set_filter_type(value, update)
    elif name == "filter_frequency":
        for voice in param_voices:
            voice.set_filter_frequency(value, update)
    elif name == "filter_resonance":
        for voice in param_voices:
            voice.set_filter_resonance(value, update)

    elif name == "waveform":
        for voice in param_voices:
            voice.set_waveform(value, update)
    elif name == "level":
        for voice in param_voices:
            voice.note.amplitude.offset = value
    elif name == "coarse_tune":
        for voice in param_voices:
            voice.set_coarse_tune(value, update)
    elif name == "fine_tune":
        for voice in param_voices:
            voice.set_fine_tune(value, update)

    elif name == "tremolo_rate":
        for voice in param_voices:
            voice.note.amplitude.rate = value
    elif name == "tremolo_depth":
        for voice in param_voices:
            voice.note.amplitude.scale = value

    elif name == "vibrato_rate":
        for voice in param_voices:
            voice.note.bend.rate = value
    elif name == "vibrato_depth":
        for voice in param_voices:
            voice.note.bend.scale = value

    elif name == "pan_rate":
        for voice in param_voices:
            voice.note.panning.rate = value
    elif name == "pan_depth":
        for voice in param_voices:
            voice.note.panning.scale = value
    elif name == "pan":
        for voice in param_voices:
            voice.note.panning.offset = map_value(value, -1.0, 1.0)

    elif name == "attack_time":
        for voice in param_voices:
            voice.set_envelope_attack_time(value, update)
    elif name == "decay_time":
        for voice in param_voices:
            voice.set_envelope_decay_time(value, update)
    elif name == "release_time":
        for voice in param_voices:
            voice.set_envelope_release_time(value, update)
    elif name == "attack_level":
        for voice in param_voices:
            voice.set_envelope_attack_level(value, update)
    elif name == "sustain_level":
        for voice in param_voices:
            voice.set_envelope_sustain_level(value, update)

def read_json(path):
    try:
        with open(path, "r") as file:
            data = json.load(file)
    except:
        print("Failed to read JSON file:", path)
        return None
    return data

def save_json(path, data):
    if not data:
        return False
    try:
        with open(path, "w") as file:
            json.dump(data, file)
    except:
        print("Failed to write JSON file:", path)
        return False
    return True

def read_patch(path):
    data = read_json(path)
    if not data:
        return False
    for name in data:
        set_parameter(name, data[name], False)
    for voice in voices:
        voice.update_waveform()
        voice.update_filter()
        voice.update_envelope()
        voice.update_bend()
    keyboard.update()

def control_change(control, value):
    name = None
    if control == 1: # Mod Wheel
        name = cc_map.get(cc_mod, None)
    elif control == 64: # Sustain
        keyboard.set_sustain(value)
    else:
        name = cc_map.get(control, None)
    if name:
        set_parameter(name, value)

def pitch_bend(value):
    voice.set_bend(value)

while True:
    msg = midi.receive()
    if msg != None:
        if midi_thru:
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
