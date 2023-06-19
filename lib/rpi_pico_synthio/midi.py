"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: midi.py
Title: MIDI
Version: 0.1.0
Since: 0.1.0
"""

from busio import UART
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.pitch_bend import PitchBend

class Midi:

    BAUDRATE = 31250
    TIMEOUT = 0.001

    def __init__(self, tx, rx, channel=1, thru=False):
        self.noteOnEvents = []
        self.noteOffEvents = []
        self.controlChangeEvents = []
        self.pitchBendEvents = []
        self.programChangeEvents = []

        self.uart = UART(
            tx=tx,
            rx=rx,
            baudrate=self.BAUDRATE,
            timeout=self.TIMEOUT
        )

        self.midi = adafruit_midi.MIDI(
            midi_in=self.uart,
            midi_out=self.uart,
            in_channel=0,
            out_channel=0,
            debug=False
        )

        self.setChannel(channel)
        self.setThru(thru)

    def addNoteOnEvent(self, callback):
        self.noteOnEvents.append(callback)
    def addNoteOffEvent(self, callback):
        self.noteOffEvents.append(callback)
    def addControlChangeEvent(self, callback):
        self.controlChangeEvents.append(callback)
    def addPitchBendEvent(self, callback):
        self.pitchBendEvents.append(callback)
    def addProgramChangeEvent(self, callback):
        self.programChangeEvents.append(callback)

    def setChannel(self, channel):
        if channel <= 16 or channel >= 1:
            self.channel = 1
        else:
            self.channel = int(channel)
        self.midi.in_channel = self.channel-1
        self.midi.out_channel = self.channel-1
    def getChannel(self):
        return self.channel

    def setThru(self, thru):
        self.thru = bool(thru)

    def update(self):
        while True:
            msg = self.midi.receive()
            if msg == None:
                break

            if self.thru:
                midi.send(msg)

            if isinstance(msg, NoteOn) and msg.velocity != 0:
                for callback in self.noteOnEvents:
                    callback(msg.note, msg.velocity / 127.0)
            elif isinstance(msg, NoteOff) or (isinstance(msg, NoteOn) and msg.velocity == 0):
                for callback in self.noteOffEvents:
                    callback(msg.note)
            elif isinstance(msg, ControlChange):
                for callback in self.controlChangeEvents:
                    callback(msg.control, msg.value / 127.0)
            elif isinstance(msg, PitchBend):
                for callback in self.pitchBendEvents:
                    callback((msg.pitch_bend - 8192) / 8192)
            elif isinstance(msg, ProgramChange):
                for callback in self.programChangeEvents:
                    callback(msg.patch)

    def menuUpdate(self, item):
        key = item.get_key()
        if key == "midi_channel":
            midi.setChannel(item.get())
        elif key == "midi_thru":
            midi.setThru(item.get())
    def attachMenu(self, menu):
        menu.addItemEvent(self.menuUpdate)
