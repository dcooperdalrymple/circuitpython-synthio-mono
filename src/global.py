# Modules

import gc, os, sys, time, math, random, board
import ulab.numpy as numpy
import synthio
from audiomixer import Mixer

from busio import UART
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.pitch_bend import PitchBend

from digitalio import DigitalInOut, Direction, Pull
from rotaryio import IncrementalEncoder
from adafruit_debouncer import Button

def free_module(mod):
    if type(mod) is tuple:
        for _mod in mod:
            free_module(_mod)
    else:
        name = mod.__name__
        if name in sys.modules:
            del sys.modules[name]
        gc.collect()
def free_all_modules():
    for name in sys.modules:
        del sys.modules[name]
    gc.collect()

# JSON

def read_json(path):
    import json
    data = None
    try:
        with open(path, "r") as file:
            data = json.load(file)
        print("Successfully read JSON file: {}".format(path))
    except:
        print("Failed to read JSON file: {}".format(path))
    free_module(json)
    del json
    return data
def save_json(path, data):
    import json
    if not data:
        return False
    result = False
    try:
        with open(path, "w") as file:
            json.dump(data, file)
        print("Successfully written JSON file: {}".format(path))
        result = True
    except:
        print("Failed to write JSON file: {}".format(path))
    free_module(json)
    del json
    return result

# Mapping

def map_value(value, min_value, max_value):
    value = min(max(value, 0.0), 1.0)
    value = (value * (max_value - min_value)) + min_value
    if type(min_value) is int:
        return round(value)
    else:
        return value
def unmap_value(value, min_value, max_value):
    return (min(max(value, min_value), max_value) - min_value) / (max_value - min_value)

def map_value_centered(value, min_value, center_value, max_value, threshold=0.0):
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
def unmap_value_centered(value, min_value, center_value, max_value, threshold=0.0):
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

# Strings

def truncate_str(value, length, right_aligned=False):
    if not type(value) is str:
        value = str(value)
    if len(value) > length:
        value = value[:length]
    elif len(value) < length:
        if right_aligned:
            value = " " * (length - len(value)) + value
        else:
            value = value + " " * (length - len(value))
    return value

# Settings

def getenvgpio(key, default=None):
    return getattr(board, os.getenv(key, default), None)

def getenvfloat(key, default=0.0, decimals=2):
    mod=math.pow(10.0,decimals*1.0)
    return os.getenv(key, default*mod)/mod

def getenvbool(key, default=False):
    default = 1 if default else 0
    return os.getenv(key, 1 if default else 0) > 0
