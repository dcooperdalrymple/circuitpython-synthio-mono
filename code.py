# circuitpython-synthio-mono
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time, math, random, board

from digitalio import DigitalInOut, Direction, Pull
from rotaryio import IncrementalEncoder
from adafruit_debouncer import Debouncer

import os, storage, json, re
import adafruit_wave

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

from busio import I2C
import displayio, adafruit_displayio_ssd1306, terminalio
from adafruit_display_text import label

import synthio
import ulab.numpy as numpy

# Program Constants

MAP_THRESHOLD       = 0.0

MIDI_CHANNEL_MAX    = 15
MIDI_CHANNEL_MIN    = 0
MIDI_TX             = board.GP4
MIDI_RX             = board.GP5
MIDI_UPDATE         = 0.05

I2S_CLK             = board.GP0
I2S_WS              = board.GP1
I2S_DATA            = board.GP2

DISPLAY_ADDRESS     = 0x3c
DISPLAY_WIDTH       = 128
DISPLAY_HEIGHT      = 32
DISPLAY_I2C_SCL     = board.GP21
DISPLAY_I2C_SDA     = board.GP20
DISPLAY_I2C_SPEED   = 1000000 # 1Mhz (Fast Mode Plus), 400kHz (Fast Mode) or 100kHz (Standard Mode)
DISPLAY_UPDATE      = 0.2

ENCODER_A           = board.GP12
ENCODER_B           = board.GP13
ENCODER_BTN         = board.GP7
ENCODER_UPDATE      = 0.1

SAMPLE_RATE         = 22050
BUFFER_SIZE         = 4096

WAVE_SAMPLES        = 256
WAVE_AMPLITUDE      = 12000 # out of 16384

COARSE_TUNE         = 2.0
FINE_TUNE           = 1.0/12.0
BEND_AMOUNT         = 1.0

FILTER_FREQ_MAX     = min(SAMPLE_RATE*0.45, 20000.0)
FILTER_FREQ_MIN     = 60.0
FILTER_RES_MAX      = 16.0
FILTER_RES_MIN      = 0.25

ENVELOPE_TIME_MAX   = 2.0
ENVELOPE_TIME_MIN   = 0.05

GLIDE_MAX           = 2.0
GLIDE_MIN           = 0.05

# Release REPL
displayio.release_displays()

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("circuitpython-synthio-mono")
print("Version 1.0")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/circuitpython-synthio-mono/")

print("\n:: Initializing Display ::")

class Display:
    def __init__(self):
        self._queued = None
    def set_title(self, text):
        pass
    def set_group(self, text):
        pass
    def set_value(self, text):
        pass
    def queue(self, title, group, value):
        self._queued = (title, group, value)
    def update(self):
        if self._queued:
            self.set_title(self._queued[0])
            self.set_group(self._queued[1])
            self.set_value(self._queued[2])
            self._queued = None
    def set_selected(self, value):
        pass

class DisplaySSD1306(Display):
    def __init__(self, scl=DISPLAY_I2C_SCL, sda=DISPLAY_I2C_SDA, speed=DISPLAY_I2C_SPEED, address=DISPLAY_ADDRESS, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT):
        self._width = width
        self._height = height

        self._i2c = I2C(
            scl=scl,
            sda=sda,
            frequency=speed
        )
        self._bus = displayio.I2CDisplay(
            self._i2c,
            device_address=address
        )
        self._driver = adafruit_displayio_ssd1306.SSD1306(
            self._bus,
            width=self._width,
            height=self._height
        )

        self._group = displayio.Group()
        self._driver.show(self._group)

        self._bg_bitmap = displayio.Bitmap(self._width, self._height, 1)
        self._bg_palette = displayio.Palette(1)
        self._bg_palette[0] = 0x000000
        self._bg_sprite = displayio.TileGrid(
            self._bg_bitmap,
            pixel_shader=self._bg_palette,
            x=0,
            y=0
        )
        self._group.append(self._bg_sprite)

        self._title_label = label.Label(
            terminalio.FONT,
            text="",
            color=0xFFFFFF,
            background_color=None
        )
        self._group.append(self._title_label)

        self._group_label = label.Label(
            terminalio.FONT,
            text="",
            color=0x000000,
            background_color=0xFFFFFF
        )
        self._group.append(self._group_label)

        self._value_label = label.Label(
            terminalio.FONT,
            text="",
            color=0xFFFFFF,
            background_color=None
        )
        self._group.append(self._value_label)

        super().__init__()
    def set_title(self, text):
        self._title_label.text = str(text)
    def set_group(self, text):
        self._group_label.text = str(text)
    def set_value(self, text):
        if type(text) == type(0.5):
            text = "{:.2f}".format(text)
        self._value_label.text = str(text)
    def set_selected(self, value):
        if value:
            self._title_label.color = 0x000000
            self._title_label.background_color = 0xFFFFFF
        else:
            self._title_label.color = 0xFFFFFF
            self._title_label.background_color = 0x000000

class DisplaySSD1306_128x32(DisplaySSD1306):
    def __init__(self, scl=DISPLAY_I2C_SCL, sda=DISPLAY_I2C_SDA, speed=DISPLAY_I2C_SPEED, address=DISPLAY_ADDRESS):
        super().__init__(scl, sda, speed, address, 128, 32)
        self._title_label.anchor_point = (0.0,0.5)
        self._title_label.anchored_position = (0,self._height//4)
        self._group_label.anchor_point = (1.0,0.5)
        self._group_label.anchored_position = (self._width,self._height//4)
        self._value_label.anchor_point = (0.0,0.5)
        self._value_label.anchored_position = (0,self._height//4*3)

class DisplaySSD1306_128x64(DisplaySSD1306):
    def __init__(self, scl=DISPLAY_I2C_SCL, sda=DISPLAY_I2C_SDA, speed=DISPLAY_I2C_SPEED, address=DISPLAY_ADDRESS):
        super().__init__(scl, sda, speed, address, 128, 64)
        self._group_label.anchor_point = (0.5,0.5)
        self._group_label.anchored_position = (self._width//2,self._height//8)
        self._title_label.anchor_point = (0.5,0.5)
        self._title_label.anchored_position = (self._width//2,self._height//8*3)
        self._value_label.anchor_point = (0.5,0.5)
        self._value_label.anchored_position = (self._width//2,self.height//4*3)

display = DisplaySSD1306_128x32()
display.set_title("circuitpython-synthio-mono v1.0")
display.set_value("Loading...")

print("\n:: Initializing Encoder ::")

class Encoder:
    def __init__(self, pin_a, pin_b, pin_button):
        self._encoder = IncrementalEncoder(pin_a, pin_b)
        self._position = None
        self._button_pin = DigitalInOut(pin_button)
        self._button_pin.direction = Direction.INPUT
        self._button_pin.pull = Pull.UP
        self._button = Debouncer(self._button_pin)
        self._increment = None
        self._decrement = None
        self._press = None
        self._release = None
    def set_increment(self, callback):
        self._increment = callback
    def set_decrement(self, callback):
        self._decrement = callback
    def set_press(self, callback):
        self._press = callback
    def set_release(self, callback):
        self._release = callback
    def update(self):
        position = self._encoder.position
        if not self._position is None and position != self._position:
            p = position
            if position > self._position and self._increment:
                while p > self._position:
                    p=p-1
                    self._increment()
            elif position < self._position and self._decrement:
                while p < self._position:
                    p=p+1
                    self._decrement()
        self._position = position
        self._button.update()
        if self._button.fell and self._press:
            self._press()
        elif self._button.rose and self._release:
            self._release()
    def deinit(self):
        self._encoder.deinit()
encoder = Encoder(ENCODER_A, ENCODER_B, ENCODER_BTN)

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
usb_midi_driver = adafruit_midi.MIDI(
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

waveforms = [
    {
        "name": "saw",
        "data": numpy.linspace(WAVE_AMPLITUDE, -WAVE_AMPLITUDE, num=WAVE_SAMPLES, dtype=numpy.int16)
    },
    {
        "name": "reverse_saw",
        "data": numpy.array(numpy.flip(numpy.linspace(WAVE_AMPLITUDE, -WAVE_AMPLITUDE, num=WAVE_SAMPLES, dtype=numpy.int16)), dtype=numpy.int16)
    },
    {
        "name": "square",
        "data": numpy.concatenate((numpy.ones(WAVE_SAMPLES//2, dtype=numpy.int16)*WAVE_AMPLITUDE,numpy.ones(WAVE_SAMPLES//2, dtype=numpy.int16)*-WAVE_AMPLITUDE))
    },
    {
        "name": "sine",
        "data": numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, WAVE_SAMPLES, endpoint=False)) * WAVE_AMPLITUDE, dtype=numpy.int16)
    },
    {
        "name": "noise",
        "data": numpy.array([random.randint(-WAVE_AMPLITUDE, WAVE_AMPLITUDE) for i in range(WAVE_SAMPLES)], dtype=numpy.int16)
    }
]

print("Appending Wav File Waveforms")

def get_waveform_by_name(name, index=False):
    global waveforms
    for i in range(len(waveforms)):
        if waveforms[i].get("name", "") == name:
            if index:
                return i
            else:
                return waveforms[i]
    if index:
        return 0
    else:
        return None

def read_waveform(filename):
    with adafruit_wave.open("/waveforms/"+filename) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            print("Failed to read {}: unsupported format".format(filename))
            return None
        # Read into numpy array, resize (with linear interpolation) into designated buffer size, and normalize
        data = numpy.frombuffer(w.readframes(w.getnframes()), dtype=numpy.int16)
        data = numpy.array(numpy.interp(numpy.linspace(0,1,WAVE_SAMPLES), numpy.linspace(0,1,data.size), data), dtype=numpy.int16)
        norm = max(numpy.max(data), abs(numpy.min(data)))
        if not norm:
            return data
        return numpy.array(data*(WAVE_AMPLITUDE/norm), dtype=numpy.int16)
    return None
def valid_waveform_filename(filename):
    return len(filename) > len("a.wav") and filename[-4:] == ".wav"
def get_waveform_name(filename):
    if not valid_waveform_filename(filename):
        return ""
    return str(filename[:-4])
def list_waveforms():
    try:
        return [filename for filename in os.listdir("/waveforms") if valid_waveform_filename(filename)]
    except:
        return []

waveform_files = list_waveforms()
if waveform_files:
    for filename in waveform_files:
        if valid_waveform_filename(filename):
            waveforms.append({
                "name": get_waveform_name(filename),
                "data": read_waveform(filename)
            })

print("Generating Synth")
synth = synthio.Synthesizer(
    sample_rate=SAMPLE_RATE,
    channel_count=2
)
mixer.voice[0].play(synth)

print("Building Voice")
filter_types = ["lpf", "hpf", "bpf"]

def map_value(value, min_value, max_value):
    value = min(max(value, 0.0), 1.0)
    value = (value * (max_value - min_value)) + min_value
    if type(min_value) is int:
        return round(value)
    else:
        return value
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

def map_array(value, arr, index=False):
    if type(value) == type(""):
        if not value in arr:
            i = 0
        else:
            i = arr.index(value)
    else:
        i = math.floor(max(min(value * len(arr), len(arr) - 1), 0))
    if index:
        return i
    else:
        return arr[i]
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

class LerpBlockInput:
    def __init__(self, rate=1.0, value=0.0):
        self.position = synthio.LFO(
            waveform=numpy.linspace(-16385, 16385, num=2, dtype=numpy.int16),
            rate=1/rate,
            scale=1.0,
            offset=0.5,
            once=True
        )
        synth.blocks.append(self.position)
        self.lerp = synthio.Math(synthio.MathOperation.CONSTRAINED_LERP, value, value, self.position)
        synth.blocks.append(self.lerp)
    def get(self):
        return self.lerp
    def set(self, value):
        self.lerp.a = self.lerp.value
        self.lerp.b = value
        self.position.retrigger()
    def set_rate(self, value):
        self.position.rate = 1/value
    def get_rate(self):
        return self.position.rate

class Oscillator:
    def __init__(self, root=440.0):
        self._log2 = math.log(2) # for octave conversion optimization

        self.coarse_tune = 0.0
        self.fine_tune = 0.0
        self.bend_amount = 0.0
        self.bend = 0.0

        self.root = root
        self.frequency_lerp = LerpBlockInput()
        self.vibrato = synthio.LFO(
            waveform=get_waveform_by_name("sine").get("data", None),
            rate=1.0,
            scale=0.0,
            offset=0.0
        )
        self.pitch_bend_lerp = LerpBlockInput(rate=GLIDE_MIN)
        self.note = synthio.Note(
            waveform=None,
            frequency=root,
            amplitude=synthio.LFO( # Tremolo
                waveform=get_waveform_by_name("sine").get("data", None),
                rate=1.0,
                scale=0.0,
                offset=1.0
            ),
            bend=synthio.Math(synthio.MathOperation.SUM, self.frequency_lerp.get(), self.vibrato, self.pitch_bend_lerp.get()),
            panning=synthio.LFO( # Panning
                waveform=get_waveform_by_name("sine").get("data", None),
                rate=1.0,
                scale=0.0,
                offset=0.0
            )
        )
        synth.blocks.append(self.note.amplitude)
        synth.blocks.append(self.note.bend)
        synth.blocks.append(self.note.panning)

    def set_frequency(self, value):
        self.frequency_lerp.set(math.log(value/self.root)/self._log2)
    def set_glide(self, value):
        self.frequency_lerp.set_rate(value)

    def set_pitch_bend_amount(self, value):
        self.bend_amount = value
        self._update_pitch_bend()
    def set_pitch_bend(self, value=None):
        self.bend = value
        self._update_pitch_bend()
    def _update_pitch_bend(self):
        self.pitch_bend_lerp.set(self.bend * self.bend_amount)

    def set_coarse_tune(self, value):
        self.coarse_tune = value
        self._update_root()
    def set_fine_tune(self, value):
        self.fine_tune = value
        self._update_root()
    def _update_root(self):
        self.note.frequency = self.root * pow(2,self.coarse_tune) * pow(2,self.fine_tune)

    def set_waveform(self, value):
        waveform = None
        if type(value) is int:
            waveform = waveforms[value]
        elif type(value) is str:
            waveform = get_waveform_by_name(value)
        if not waveform:
            self.note.waveform = None
        else:
            self.note.waveform = waveform.get("data", None)

    def press(self):
        synth.press(self.note)
    def release(self):
        synth.release(self.note)

    def set_envelope(self, envelope):
        self.note.envelope = envelope
    def set_filter(self, filter):
        self.note.filter = filter

    def set_level(self, value):
        self.note.amplitude.offset = value
    def set_tremolo_rate(self, value):
        self.note.amplitude.rate = value
    def set_tremolo_depth(self, value):
        self.note.amplitude.scale = value
    def set_vibrato_rate(self, value):
        self.vibrato.rate = value
    def set_vibrato_depth(self, value):
        self.vibrato.scale = value
    def set_pan_rate(self, value):
        self.note.panning.rate = value
    def set_pan_depth(self, value):
        self.note.panning.scale = value
    def set_pan(self, value):
        self.note.panning.offset = value

class Voice:
    def __init__(self):
        self.note = -1
        self.velocity = 0.0

        self.velocity_amount = 1.0
        self.attack_time = 0.0
        self.decay_time = 0.0
        self.release_time = 0.0
        self.attack_level = 1.0
        self.sustain_level = 0.75

        self.filter_type = 0
        self._filter_type = self.filter_type
        self.filter_frequency = 1.0
        self.filter_resonance = 0.0

        self.oscillators = (Oscillator(), Oscillator())

    def press(self, note, velocity):
        self.velocity = velocity
        self._update_envelope()
        if note != self.note:
            frequency = synthio.midi_to_hz(note)
            for oscillator in self.oscillators:
                oscillator.set_frequency(frequency)
                oscillator.press()
    def release(self):
        for oscillator in self.oscillators:
            oscillator.release()
        self.note = -1

    def set_glide(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_glide(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_glide(value)

    def set_pitch_bend_amount(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_pitch_bend_amount(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_pitch_bend_amount(value)
    def set_pitch_bend(self, value):
        for oscillator in self.oscillators:
            oscillator.set_pitch_bend(value)

    def set_coarse_tune(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_coarse_tune(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_coarse_tune(value)
    def set_fine_tune(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_fine_tune(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_fine_tune(value)

    def set_waveform(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_waveform(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_waveform(value)

    def _build_filter(self):
        type = self.get_filter_type()
        if type == "lpf":
            return synth.low_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
        elif type == "hpf":
            return synth.high_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
        else: # "bpf"
            return synth.band_pass_filter(self.get_filter_frequency(), self.get_filter_resonance())
    def _update_filter(self):
        filter = self._build_filter()
        for oscillator in self.oscillators:
            oscillator.set_filter(filter)
    def get_filter_type(self):
        if type(self.filter_type) is int:
            return filter_types[self.filter_type]
        elif type(self.filter_type) is str:
            return self.filter_type
        else:
            return None
    def set_filter_type(self, value, update=True):
        self.filter_type = value
        if update and self.filter_type != self._filter_type:
            self._filter_type = self.filter_type
            self._update_filter()
    def set_filter_frequency(self, value, update=True):
        self.filter_frequency = value
        if update:
            self._update_filter()
    def get_filter_frequency(self):
        return self.filter_frequency
    def set_filter_resonance(self, value, update=True):
        self.filter_resonance = value
        if update:
            self._update_filter()
    def get_filter_resonance(self):
        return self.filter_resonance

    def _get_velocity_mod(self):
        return 1.0 - (1.0 - self.velocity) * self.velocity_amount
    def _build_envelope(self):
        mod = self._get_velocity_mod()
        return synthio.Envelope(
            attack_time=self.attack_time,
            decay_time=self.decay_time,
            release_time=self.release_time,
            attack_level=mod*self.attack_level,
            sustain_level=mod*self.sustain_level
        )
    def _update_envelope(self):
        envelope = self._build_envelope()
        for oscillator in self.oscillators:
            oscillator.set_envelope(envelope)
    def set_velocity_amount(self, value):
        self.velocity_amount = value
    def set_envelope_attack_time(self, value, update=True):
        self.attack_time = value
        if update:
            self._update_envelope()
    def get_envelope_attack_time(self):
        return self.attack_time
    def set_envelope_decay_time(self, value, update=True):
        self.decay_time = value
        if update:
            self._update_envelope()
    def get_envelope_decay_time(self):
        return self.decay_time
    def set_envelope_release_time(self, value, update=True):
        self.release_time = value
        if update:
            self._update_envelope()
    def get_envelope_release_time(self):
        return self.release_time
    def set_envelope_attack_level(self, value, update=True):
        self.attack_level = value
        if update:
            self._update_envelope()
    def get_envelope_attack_level(self):
        return self.attack_level
    def set_envelope_sustain_level(self, value, update=True):
        self.sustain_level = value
        if update:
            self._update_envelope()
    def get_envelope_sustain_level(self):
        return self.sustain_level

    def set_pan(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_pan(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_pan(value)

voice = Voice()

print("Managing Keyboard")

note_types = ["high", "low", "last"]
class Keyboard:
    def __init__(self):
        self.notes = []
        self.type = 0
        self.sustain = False
        self.sustained = []

    def get_sustain(self):
        return self.sustain
    def set_sustain(self, value, update=True):
        value = map_boolean(value)
        if value != self.sustain:
            self.sustain = value
            self.sustained = []
            if self.sustain:
                self.sustained = self.notes.copy()
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
                if note[0] < selected[0]:
                    selected = note
        return selected
    def _get_high(self):
        if not self._has_notes():
            return None
        selected = (0, 0)
        if self.notes:
            for note in self.notes:
                if note[0] > selected[0]:
                    selected = note
        if self.sustain and self.sustained:
            for note in self.sustained:
                if note[0] > selected[0]:
                    selected = note
        return selected
    def _get_last(self):
        if self.sustain and self.sustained:
            return self.sustained[-1]
        if self.notes:
            return self.notes[-1]
        return None
    def get(self):
        type = note_types[self.type]
        if type == "high":
            return self._get_high()
        elif type == "low":
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
            voice.release()
        else:
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

class Parameter:
    def __init__(self, name="", label="", group="", range=None, value=0.0, set_callback=None, set_argument=None, object=None, property=None, mod=True, patch=True):
        self.name = name
        self.label = label
        self.group = group
        self.range = range
        self.set_callback = set_callback
        self.set_argument = set_argument
        self.object = object
        self.property = property
        self.mod = mod
        self.patch = patch
        self.set(value)
    def set(self, value):
        if type(value) is str:
            if type(self.range) is dict:
                value = unmap_dict(value, self.range)
            elif type(self.range) is list:
                value = unmap_array(value, self.range)
        value = min(max(value, 0.0), 1.0)
        if hasattr(self, "raw_value") and value == self.raw_value:
            return False
        self.raw_value = value
        if type(self.range) is dict:
            value = map_dict(value, self.range)
        elif type(self.range) is list:
            value = map_array(value, self.range, True)
        elif type(self.range) is tuple:
            if len(self.range) == 4: # Centered with threshold
                value = map_value_centered(value, self.range[0], self.range[1], self.range[2], self.range[3])
            elif len(self.range) == 3: # Centered
                value = map_value_centered(value, self.range[0], self.range[1], self.range[2])
            elif len(self.range) == 2: # Linear range
                value = map_value(value, self.range[0], self.range[1])
        elif type(self.range) is int or type(self.range) is float: # +/- linear range
            value = map_value(value, -self.range, self.range)
        elif type(self.range) is bool:
            value = map_boolean(value)
        self.format_value = value
        if self.set_callback:
            if self.set_argument:
                self.set_callback(value, self.set_argument)
            else:
                self.set_callback(value)
        elif self.object and self.property:
            if type(self.object) is dict:
                self.object[self.property] = value
            elif hasattr(self.object, self.property):
                setattr(self.object, self.property, value)
        return True
    def get(self):
        return self.raw_value
    def get_formatted_value(self, translate=True):
        if translate:
            value = None
            if type(self.range) is dict:
                value = list(self.range)[self.format_value]
            elif type(self.range) is list:
                value = self.range[self.format_value]
            if value:
                if type(value) is str:
                    return value
                elif type(value) is dict:
                    if value.get("label", None):
                        return value.get("label")
                    elif value.get("name", None):
                        return value.get("name")
                elif hasattr(value, "label"):
                    return value.label
                elif hasattr(value, "name"):
                    return value.name
        return self.format_value
    def get_steps(self):
        if type(self.range) is dict or type(self.range) is list:
            return len(self.range)-1
        elif type(self.range) is bool:
            return 1
        else:
            return 20
    def get_step_size(self):
        return 1.0/self.get_steps()
    def increment(self):
        return self.set(self.raw_value + self.get_step_size())
    def decrement(self):
        return self.set(self.raw_value - self.get_step_size())

class ParameterGroup:
    def __init__(self, name="", label=""):
        self.name = name
        self.label = label
        self.items = []
    def append(self, item):
        self.items.append(item)

class Parameters:
    def __init__(self):
        self.mod_parameter = 0
        self.mod_parameters = []

        self.items = [

            # Global
            Parameter(
                name="midi_channel",
                label="MIDI Channel",
                group="global",
                range=(MIDI_CHANNEL_MIN, MIDI_CHANNEL_MAX),
                set_callback=self.set_midi_channel,
                mod=False,
                patch=False
            ),
            Parameter(
                name="midi_thru",
                label="MIDI Thru",
                group="global",
                range=True,
                set_callback=self.set_midi_thru,
                mod=False,
                patch=False
            ),
            Parameter(
                name="volume",
                label="Volume",
                group="global",
                value=1.0,
                object=mixer.voice[0],
                property="level"
            ),
            Parameter(
                name="glide",
                label="Glide",
                group="global",
                range=(GLIDE_MIN,GLIDE_MAX),
                set_callback=voice.set_glide,
                patch=False
            ),
            Parameter(
                name="keyboard_type",
                label="Note Type",
                group="global",
                range=note_types,
                object=keyboard,
                property="type"
            ),
            Parameter(
                name="velocity_amount",
                label="Velocity Amount",
                group="global",
                set_callback=voice.set_velocity_amount
            ),
            Parameter(
                name="bend_amount",
                label="Bend Amount",
                group="global",
                range=BEND_AMOUNT,
                value=1.0,
                set_callback=voice.set_pitch_bend_amount,
                patch=False
            ),
            Parameter(
                name="mod_parameter",
                label="Mod Wheel",
                group="global",
                range=self.mod_parameters,
                object=self,
                property="mod_parameter"
            ),

            # Voice
            Parameter(
                name="waveform",
                label="Waveform",
                group="voice",
                range=waveforms,
                set_callback=voice.set_waveform
            ),
            Parameter(
                name="filter_type",
                label="Filter",
                group="voice",
                range=filter_types,
                set_callback=voice.set_filter_type
            ),
            Parameter(
                name="filter_frequency",
                label="Frequency",
                group="voice",
                range=(FILTER_FREQ_MIN,FILTER_FREQ_MAX),
                value=1.0,
                set_callback=voice.set_filter_frequency
            ),
            Parameter(
                name="filter_resonance",
                label="Resonace",
                group="voice",
                range=(FILTER_RES_MIN, FILTER_RES_MAX),
                set_callback=voice.set_filter_resonance
            ),
            Parameter(
                name="pan",
                label="Pan",
                group="voice",
                range=1.0,
                value=0.5,
                set_callback=voice.set_pan,
                patch=False
            ),
            Parameter(
                name="attack_time",
                label="Attack Time",
                group="voice",
                range=(ENVELOPE_TIME_MIN,ENVELOPE_TIME_MAX),
                set_callback=voice.set_envelope_attack_time
            ),
            Parameter(
                name="decay_time",
                label="Decay Time",
                group="voice",
                range=(ENVELOPE_TIME_MIN,ENVELOPE_TIME_MAX),
                set_callback=voice.set_envelope_decay_time
            ),
            Parameter(
                name="release_time",
                label="Release Time",
                group="voice",
                range=(ENVELOPE_TIME_MIN,ENVELOPE_TIME_MAX),
                set_callback=voice.set_envelope_release_time
            ),
            Parameter(
                name="attack_level",
                label="Attack Level",
                group="voice",
                value=1.0,
                set_callback=voice.set_envelope_attack_level
            ),
            Parameter(
                name="sustain_level",
                label="Sustain Level",
                group="voice",
                value=1.0,
                set_callback=voice.set_envelope_sustain_level
            ),

            # Oscillator 1
            Parameter(
                name="glide_0",
                label="Glide",
                group="osc0",
                range=(GLIDE_MIN,GLIDE_MAX),
                set_callback=voice.oscillators[0].set_glide
            ),
            Parameter(
                name="bend_amount_0",
                label="Bend Amount",
                group="osc0",
                range=BEND_AMOUNT,
                value=1.0,
                set_callback=voice.oscillators[0].set_pitch_bend_amount
            ),
            Parameter(
                name="waveform_0",
                label="Waveform",
                group="osc0",
                range=waveforms,
                set_callback=voice.oscillators[0].set_waveform
            ),
            Parameter(
                name="level_0",
                label="Level",
                group="osc0",
                value=1.0,
                set_callback=voice.oscillators[0].set_level
            ),
            Parameter(
                name="coarse_tune_0",
                label="Coarse Tune",
                group="osc0",
                range=COARSE_TUNE,
                value=0.5,
                set_callback=voice.oscillators[0].set_coarse_tune
            ),
            Parameter(
                name="fine_tune_0",
                label="Fine Tune",
                group="osc0",
                range=FINE_TUNE,
                value=0.5,
                set_callback=voice.oscillators[0].set_fine_tune
            ),
            Parameter(
                name="tremolo_rate_0",
                label="Tremolo Rate",
                group="osc0",
                set_callback=voice.oscillators[0].set_tremolo_rate
            ),
            Parameter(
                name="tremolo_depth_0",
                label="Tremolo Depth",
                group="osc0",
                set_callback=voice.oscillators[0].set_tremolo_depth
            ),
            Parameter(
                name="vibrato_rate_0",
                label="Vibrato Rate",
                group="osc0",
                set_callback=voice.oscillators[0].set_vibrato_rate
            ),
            Parameter(
                name="vibrato_depth_0",
                label="Vibrato Depth",
                group="osc0",
                set_callback=voice.oscillators[0].set_vibrato_depth
            ),
            Parameter(
                name="pan_0",
                label="Pan",
                group="osc0",
                value=0.5,
                set_callback=voice.oscillators[0].set_pan
            ),
            Parameter(
                name="pan_rate_0",
                label="Panning Rate",
                group="osc0",
                set_callback=voice.oscillators[0].set_pan_rate
            ),
            Parameter(
                name="pan_depth_0",
                label="Panning Depth",
                group="osc0",
                set_callback=voice.oscillators[0].set_pan_depth
            ),

            # Oscillator 2
            Parameter(
                name="glide_1",
                label="Glide",
                group="osc1",
                range=(GLIDE_MIN,GLIDE_MAX),
                set_callback=voice.oscillators[1].set_glide
            ),
            Parameter(
                name="bend_amount_1",
                label="Bend Amount",
                group="osc1",
                range=BEND_AMOUNT,
                value=1.0,
                set_callback=voice.oscillators[1].set_pitch_bend_amount
            ),
            Parameter(
                name="waveform_1",
                label="Waveform",
                group="osc1",
                range=waveforms,
                set_callback=voice.oscillators[1].set_waveform
            ),
            Parameter(
                name="level_1",
                label="Level",
                group="osc1",
                value=0.0,
                set_callback=voice.oscillators[1].set_level
            ),
            Parameter(
                name="coarse_tune_1",
                label="Coarse Tune",
                group="osc1",
                range=COARSE_TUNE,
                value=0.5,
                set_callback=voice.oscillators[1].set_coarse_tune
            ),
            Parameter(
                name="fine_tune_1",
                label="Fine Tune",
                group="osc1",
                range=FINE_TUNE,
                value=0.5,
                set_callback=voice.oscillators[1].set_fine_tune
            ),
            Parameter(
                name="tremolo_rate_1",
                label="Tremolo Rate",
                group="osc1",
                set_callback=voice.oscillators[1].set_tremolo_rate
            ),
            Parameter(
                name="tremolo_depth_1",
                label="Tremolo Depth",
                group="osc1",
                set_callback=voice.oscillators[1].set_tremolo_depth
            ),
            Parameter(
                name="vibrato_rate_1",
                label="Vibrato Rate",
                group="osc1",
                set_callback=voice.oscillators[1].set_vibrato_rate
            ),
            Parameter(
                name="vibrato_depth_1",
                label="Vibrato Depth",
                group="osc1",
                set_callback=voice.oscillators[1].set_vibrato_depth
            ),
            Parameter(
                name="pan_1",
                label="Pan",
                group="osc1",
                value=0.5,
                set_callback=voice.oscillators[1].set_pan
            ),
            Parameter(
                name="pan_rate_1",
                label="Panning Rate",
                group="osc1",
                set_callback=voice.oscillators[1].set_pan_rate
            ),
            Parameter(
                name="pan_depth_1",
                label="Panning Depth",
                group="osc1",
                set_callback=voice.oscillators[1].set_pan_depth
            )

        ]

        self.groups = [
            ParameterGroup("global", "Global"),
            ParameterGroup("voice", "Voice"),
            ParameterGroup("osc0", "Osc 1"),
            ParameterGroup("osc1", "Osc 2"),
        ]

        for parameter in self.items:
            if parameter.mod:
                self.mod_parameters.append(parameter.name)
            self.get_group(parameter.group).append(parameter)

    def get_group(self, name):
        for group in self.groups:
            if group.name == name:
                return group
        return None
    def get_parameter(self, name):
        for parameter in self.items:
            if parameter.name == name:
                return parameter
        return None

    def set_midi_channel(self, value):
        uart_midi.in_channel = value
        uart_midi.out_channel = value
        usb_midi_driver.in_channel = value
        usb_midi_driver.out_channel = value
        if ble and ble_midi:
            ble_midi.in_channel = value
            ble_midi.out_channel = value
    def set_midi_thru(self, value):
        global midi_thru
        midi_thru = value
    def get_mod_parameter(self):
        if not self.mod_parameters:
            return "volume"
        return self.mod_parameters[self.mod_parameter]

parameters = Parameters()

midi_map = read_json("/midi.json")

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
    try:
        return [filename for filename in os.listdir("/patches") if valid_patch_filename(filename)]
    except:
        return []

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
        parameter = parameters.get_parameter(name)
        if parameter:
            parameter.set(data["parameters"][name])
    keyboard.update()
    print("Successfully Imported Patch")
    return True
def save_patch(index=0, name="Patch"):
    data = {
        "index": 0,
        "name": name,
        "parameters": {},
    }
    for parameter in parameters.items:
        if parameter.patch:
            data["parameters"][parameter.name] = parameter.get()
    remove_patch(index)
    path = "/patches/{:02d}-{}.json".format(index, slugify(name))
    print("Saving Patch #{:d} ({}) at {}".format(index, name, path))
    return save_json(path, data)
def read_first_patch():
    return read_patch(0)

#read_first_patch()

print("\n:: Setting Up Menu ::")

class MenuItem:
    def __init__(self, group_index=0, group=None, parameter_index=0, parameter=None):
        self.group_index = group_index
        self.group = group
        self.parameter_index = parameter_index
        self.parameter = parameter

class Menu:
    def __init__(self):
        self._item = None
        self._selected = False
    def _get_item_by_index(self, group_index, parameter_index):
        group_index = group_index % len(parameters.groups)
        group = parameters.groups[group_index]
        parameter_index = parameter_index % len(group.items)
        parameter = group.items[parameter_index]
        return MenuItem(group_index, group, parameter_index, parameter)
    def _get_item_by_name(self, name):
        parameter = parameters.get_parameter(name)
        group = parameters.get_group(parameter.group)
        return MenuItem(self._get_group_index(group), group, self._get_parameter_index(group, parameter), parameter)
    def _get_group_index(self, group):
        for i in range(len(parameters.groups)):
            if parameters.groups[i] == group:
                return i
        return 0
    def _get_parameter_index(self, group, parameter):
        for i in range(len(group.items)):
            if group.items[i] == parameter:
                return i
        return 0
    def _queue(self):
        if not self._item:
            return False
        display.queue(self._item.parameter.label, self._item.group.label, self._item.parameter.get_formatted_value())
        return True
    def _queue_by_index(self, group_index, parameter_index):
        item = self._get_item_by_index(group_index, parameter_index)
        if not item:
            return False
        self._item = item
        return self._queue()
    def display(self, name=None):
        if not name:
            return self._queue()
        if not self._item or self._item.parameter.name != name:
            self._item = self._get_item_by_name(name)
        return self._queue()
    def first(self):
        return self._queue_by_index(0, 0)
    def last(self):
        return self._queue_by_index(-1, -1)
    def next(self):
        if not self._item:
            return self.first()
        if self._item.parameter_index >= len(self._item.group.items)-1:
            return self._queue_by_index(self._item.group_index+1, 0)
        else:
            return self._queue_by_index(self._item.group_index, self._item.parameter_index+1)
    def previous(self):
        if not self._item:
            return self.last()
        if self._item.parameter_index <= 0:
            return self._queue_by_index(self._item.group_index-1, -1)
        else:
            return self._queue_by_index(self._item.group_index, self._item.parameter_index-1)
    def increment(self):
        if self._selected and self._item:
            if self._item.parameter.increment():
                return self._queue()
            else:
                return False
        else:
            return self.next()
    def decrement(self):
        if self._selected and self._item:
            if self._item.parameter.decrement():
                return self._queue()
            else:
                return False
        else:
            return self.previous()
    def toggle(self):
        if self._selected:
            self.deselect()
        else:
            self.select()
    def select(self):
        self._selected = True
        display.set_selected(self._selected)
    def deselect(self):
        self._selected = False
        display.set_selected(self._selected)
    def selected(self):
        return self._selected

menu = Menu()
encoder.set_increment(menu.increment)
encoder.set_decrement(menu.decrement)
encoder.set_release(menu.toggle)

print("\n:: Initialization Complete ::")
display.set_value("Ready!")

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
def note_off(notenum):
    keyboard.remove(notenum)

def control_change(control, value):
    name = None
    if control == 1: # Mod Wheel
        name = parameters.get_mod_parameter()
    elif control == 64: # Sustain
        keyboard.set_sustain(value)
    else:
        name = midi_map.get(str(control), None)
    if name:
        parameter = parameters.get_parameter(name)
        if parameter:
            parameter.set(value)
            if control != 1:
                menu.display(name)

def pitch_bend(value):
    voice.set_pitch_bend(value)

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

    global midi_thru
    if midi_thru:
        uart_midi.send(msg)
        usb_midi_driver.send(msg)
        if ble and ble.connected and ble_midi:
            ble_midi.send(msg)

def process_midi_msgs(midi, limit=32):
    while limit>0:
        msg = midi.receive()
        if not msg:
            break
        process_midi_msg(msg)
        limit = limit - 1

last_midi_now = 0
last_encoder_now = 0
last_display_now = 0
while True:
    now = time.monotonic()

    if now >= last_midi_now + MIDI_UPDATE:
        last_midi_now = now
        process_midi_msgs(uart_midi)
        process_midi_msgs(usb_midi_driver)
        if ble and ble.connected and ble_midi:
            process_midi_msgs(ble_midi)

    if now >= last_encoder_now + ENCODER_UPDATE:
        last_encoder_now = now
        encoder.update()

    if now >= last_display_now + DISPLAY_UPDATE:
        last_display_now = now
        display.update()

print("\n:: Deinitializing ::")

print("Synthesizer")
synth.release_all()
synth.deinit()

print("Mixer")
mixer.deinit()

print("Audio")
audio.deinit()

print("Encoder")
encoder.deinit()

print("Display")
displayio.release_displays()

print("\n:: Process Ended ::")
led.value = False
