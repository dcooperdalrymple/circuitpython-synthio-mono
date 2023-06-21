# rpi-pico-synthio
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time
import math
import board

from digitalio import DigitalInOut, Direction, Pull

import os
import re
import json
import storage

from busio import UART
import usb_midi
import adafruit_ble
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
import adafruit_ble_midi
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

MAP_THRESHOLD       = 0.0

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
print("rpi-pico-synthio")
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
uart_midi = adafruit_midi.MIDI(
    midi_in=uart,
    midi_out=uart,
    in_channel=0,
    out_channel=0,
    debug=False
)

print("USB")
usb_midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    in_channel=0,
    out_channel=0,
    debug=False
)

print("Bluetooth")
try:
    ble_midi_service = adafruit_ble_midi.MIDIService()
    ble_advertisement = ProvideServicesAdvertisement(ble_midi_service)

    ble = adafruit_ble.BLERadio()
    if ble.connected:
        for c in ble.connections:
            c.disconnect()

    ble_midi = adafruit_midi.MIDI(
        midi_in=ble_midi_service,
        midi_out=ble_midi_service,
        in_channel=0,
        out_channel=0,
        debug=False
    )
except:
    ble = None
    ble_advertisement = None
    ble_midi = None
    print("Device not bluetooth capable")

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
def unmap_value(value, min_value, max_value):
    return (min(max(value, min_value), max_value) - min_value) / (max_value - min_value)

def map_value_centered(value, min_value, center_value, max_value, threshold=MAP_THRESHOLD):
    if value > 0.5 + threshold:
        if threshold > 0.0:
            value = (value-(0.5+threshold))*(1/(0.5-threshold))
        return map_value(value, center_value, max_value)
    elif value < 0.5 - threshold:
        if threshold > 0.0:
            value = value*(1/(0.5-threshold))
        return map_value(value, min_value, center_value)
    else:
        return center_value
def unmap_value_centered(value, min_value, center_value, max_value, threshold=MAP_THRESHOLD):
    if value > center_value:
        value = unmap_value(value, center_value, max_value)
        if threshold > 0.0:
            return value/(1/(0.5-threshold))+(0.5+threshold)
        else:
            return value/2+0.5
    elif value < center_value:
        value = unmap_value(value, min_value, center_value)
        if threshold > 0.0:
            return value/(1/(0.5-threshold))
        else:
            return value/2
    else:
        return 0.5

def map_boolean(value):
    if type(value) == type(False):
        return value
    else:
        return value >= 0.5
def unmap_boolean(value):
    if value:
        return 1.0
    else:
        return 0.0

def map_array(value, arr):
    if type(value) == type(""):
        if not value in arr:
            return arr[0]
        return value
    index = math.floor(max(min(value * len(arr), len(arr) - 1), 0))
    return arr[index]
def unmap_array(value, arr):
    if not value in arr:
        return 0.0
    try:
        return arr.index(value) / len(arr)
    except:
        return 0.0

def map_dict(value, dict):
    return map_array(value, list(dict))
def unmap_dict(value, dict):
    return unmap_array(value, list(dict))

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
            attack_time=self.get_envelope_attack_time(True),
            decay_time=self.get_envelope_decay_time(True),
            release_time=self.get_envelope_release_time(True),
            attack_level=self.get_velocity_mod() * self.attack_level,
            sustain_level=self.get_velocity_mod() * self.sustain_level
        )
    def update_envelope(self):
        self.note.envelope = self.build_envelope()
    def set_envelope_attack_time(self, value, update=True):
        self.attack_time = value
        if update:
            self.update_envelope()
    def get_envelope_attack_time(self, format=True):
        if format:
            return map_value(self.attack_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX)
        else:
            return self.attack_time
    def set_envelope_decay_time(self, value, update=True):
        self.decay_time = value
        if update:
            self.update_envelope()
    def get_envelope_decay_time(self, format=True):
        if format:
            return map_value(self.decay_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX)
        else:
            return self.decay_time
    def set_envelope_release_time(self, value, update=True):
        self.release_time = value
        if update:
            self.update_envelope()
    def get_envelope_release_time(self, format=True):
        if format:
            return map_value(self.release_time, ENVELOPE_TIME_MIN, ENVELOPE_TIME_MAX)
        else:
            return self.release_time
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
        if self.notes:
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

print("\n:: Reading Configuration ::")

def read_json(path):
    try:
        with open(path, "r") as file:
            data = json.load(file)
    except:
        print("Failed to read JSON file: {}".format(path))
        return None
    print("Successfully read JSON file: {}".format(path))
    return data
def save_json(path, data):
    if not data:
        return False
    try:
        with open(path, "w") as file:
            json.dump(data, file)
    except:
        print("Failed to write JSON file: {}".format(path))
        return False
    print("Successfully written JSON file: {}".format(path))
    return True

parameters = read_json("/parameters.json")
midi_map = read_json("/midi.json")

exclude_mod_parameters = [
    "midi_channel",
    "midi_thru"
]
mod_parameters = [name for name in parameters if not name in exclude_mod_parameters]
mod_parameter = mod_parameters[0]

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
        param_voices = [voices[index]]
    else:
        param_voices = voices

    if name == "midi_channel":
        value = map_value(value, MIDI_CHANNEL_MIN, MIDI_CHANNEL_MAX)
        midi.in_channel = value-1
        midi.out_channel = value-1
    elif name == "midi_thru":
        midi_thru = map_boolean(value)

    elif name == "volume":
        mixer.voice[0].level = value
    elif name == "portamento":
        pass
    elif name == "keyboard_type":
        keyboard.type = map_array(value, note_types)
    elif name == "velocity_amount":
        for voice in param_voices:
            voice.velocity_amount = value
    elif name == "bend_amount":
        for voice in param_voices:
            voice.set_bend_amount(value, update)
    elif name == "mod_parameter":
        global mod_parameter
        mod_parameter = map_array(value, mod_parameters)

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

def get_parameter(name, format=False, translate=True):
    if not name in parameters:
        return None

    index = name[-1]
    if index.isdigit():
        index = int(index)
        name = name[:len(name)-2]
        if index >= len(voices):
            return None
    else:
        index = 0
    param_voice = voices[index]

    if name == "midi_channel":
        if format:
            return midi.in_channel+1
        else:
            return unmap_value(midi.in_channel+1, MIDI_CHANNEL_MIN, MIDI_CHANNEL_MAX)
    elif name == "midi_thru":
        if format:
            return midi_thru
        else:
            return unmap_boolean(midi_thru)

    elif name == "volume":
        return value
    elif name == "portamento":
        return None # NOTE: Not implemented
    elif name == "keyboard_type":
        if format or translate:
            return keyboard.type
        else:
            return unmap_array(keyboard.type, note_types)
    elif name == "velocity_amount":
        return param_voice.velocity_amount
    elif name == "bend_amount":
        return param_voice.bend_amount
    elif name == "mod_parameter":
        global mod_parameter
        if format or translate:
            return mod_parameter
        else:
            return unmap_array(mod_parameter, mod_parameters)

    # TODO: Global filter
    elif name == "filter_type":
        if format or translate:
            return param_voice.filter_type
        else:
            return unmap_array(param_voice.filter_type, filter_types)
    elif name == "filter_frequency":
        if format:
            return param_voice.get_filter_frequency()
        else:
            return param_voice.filter_frequency
    elif name == "filter_resonance":
        if format:
            return param_voice.get_filter_resonance()
        else:
            return param_voice.filter_resonance

    elif name == "waveform":
        if format or translate:
            return param_voice.waveform
        else:
            return unmap_dict(param_voice.waveform, waveforms)
    elif name == "level":
        return param_voice.note.amplitude.offset
    elif name == "coarse_tune":
        # TODO: Formatting?
        return param_voice.coarse_tune
    elif name == "fine_tune":
        # TODO: Formatting?
        return param_voice.fine_tune

    elif name == "tremolo_rate":
        return param_voice.note.amplitude.rate
    elif name == "tremolo_depth":
        return param_voice.note.amplitude.scale

    elif name == "vibrato_rate":
        return param_voice.note.bend.rate
    elif name == "vibrato_depth":
        return param_voice.note.bend.scale

    elif name == "pan_rate":
        return param_voice.note.panning.rate
    elif name == "pan_depth":
        return param_voice.note.panning.scale
    elif name == "pan":
        if format:
            return voice.note.panning.offset
        else:
            return unmap_value(voice.note.panning.offset, -1.0, 1.0)

    elif name == "attack_time":
        return param_voice.get_envelope_attack_time(format)
    elif name == "decay_time":
        return param_voice.get_envelope_decay_time(format)
    elif name == "release_time":
        return param_voice.get_envelope_release_time(format)
    elif name == "attack_level":
        return param_voice.attack_level
    elif name == "sustain_level":
        return param_voice.sustain_level

    return None

def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')
def valid_patch_filename(filename):
    return len(filename) > len("00-a.json") and filename[-5:] == ".json" and filename[0:2].isdigit() and filename[2] == "-"
def get_patch_index(filename):
    if not valid_patch_filename(filename):
        return 0
    return int(filename[0:2])
def list_patches():
    return [filename for filename in os.listdir("/patches") if valid_patch_filename(filename)]

exclude_patch_parameters = [
    "midi_channel",
    "midi_thru",
    "portamento",
    "bend_amount",
    "pan"
]
def get_patch_filename(index):
    if type(index) == type("") and index.isdigit():
        index = int(index)
    if type(index) != type(1):
        return None
    if index > 99:
        return None
    patches = list_patches()
    if not patches:
        return None
    for filename in patches:
        if get_patch_index(filename) == index:
            return filename
    return None
def get_patch_path(index):
    filename = get_patch_filename(index)
    if not filename:
        return None
    return "/patches/{}".format(filename)
def remove_patch(index):
    path = get_patch_path(index)
    if not path:
        return False
    try:
        os.remove(path)
        return True
    except:
        return False
def read_patch(index):
    path = get_patch_path(index)
    if not path:
        return False
    print("Reading Patch #{:d}: {}".format(index, path))
    data = read_json(path)
    if not data or not "parameters" in data:
        print("Invalid Data")
        return False
    for name in data["parameters"]:
        set_parameter(name, data["parameters"][name], False)
    for voice in voices:
        voice.update_waveform()
        voice.update_filter()
        voice.update_envelope()
        voice.update_bend()
    keyboard.update()
    print("Successfully Imported Patch")
    return True
def save_patch(index=0, name="Patch"):
    data = {
        "index": 0,
        "name": name,
        "parameters": {},
    }
    for name in parameters:
        if not name in exclude_patch_parameters:
            value = get_parameter(name, False, True)
            if value:
                data["parameters"][name] = value
    remove_patch(index)
    path = "/patches/{:02d}-{}.json".format(index, slugify(name))
    print("Saving Patch #{:d} ({}) at {}".format(index, name, path))
    return save_json(path, data)
def read_first_patch():
    return read_patch(0)

read_first_patch()

print("\n:: Initialization Complete ::")

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
def note_off(notenum):
    keyboard.remove(notenum)

def control_change(control, value):
    name = None
    if control == 1: # Mod Wheel
        global mod_parameter
        name = mod_parameter
    elif control == 64: # Sustain
        keyboard.set_sustain(value)
    else:
        name = midi_map.get(str(control), None)
    if name:
        set_parameter(name, value)

def pitch_bend(value):
    for voice in voices:
        voice.set_bend(value)

if ble and ble_advertisement:
    ble.start_advertising(ble_advertisement)

def process_midi_msg(msg):
    if msg == None:
        return

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
        pitch_bend((msg.pitch_bend - 8192) / 8192)
    elif isinstance(msg, ProgramChange):
        read_patch(msg.patch)

    if midi_thru:
        uart_midi.send(msg)
        usb_midi.send(msg)
        if ble and ble.connected and ble_midi:
            ble_midi.send(msg)

while True:
    process_midi_msg(uart_midi.receive())
    process_midi_msg(usb_midi.receive())
    if ble and ble.connected and ble_midi:
        process_midi_msg(ble_midi.receive())

print("\n:: Deinitializing ::")

print("Synthesizer")
synth.release_all()
synth.deinit()

print("Mixer")
mixer.deinit()

print("Audio")
audio.deinit()

print("\n:: Process Ended ::")
led.value = False
