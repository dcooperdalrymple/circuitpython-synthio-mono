"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: config.py
Title: Config
Version: 0.1.0
Since: 0.1.0
"""

import json
import storage
from busio import SPI
from sdcardio import SDCard

class Config:

    PATH = "/config.json"
    SD_MOUNT = "/sd"
    PATCH_DIR = "/patches"

    def __init__(self):
        self.data = dict()

    def readFlashSettings(self):
        self.readFile(self.PATH)

    def initSD(self, clock, mosi, miso, cs):
        self.spi = SPI(clock, mosi, miso)
        self.sd = SDCard(self.spi, cs)
        self.vfs = storage.VfsFat(self.sd)
        storage.mount(self.vfs, self.SD_MOUNT)

    def readSDSettings(self):
        if not self.vfs:
            return
        self.readFile(self.SD_MOUNT + self.PATH)

    def readFile(self, filename):
        file = open(filename, "r")
        data = json.loads(file.read())

        self.mergeData(data)

        del data
        file.close()
        del file
        gc.collect()

    def getData(self, default, group, key=None):
        if not group in self.data or (key != None and not key in self.data[group]):
            return default
        if key != None:
            return self.data[group][key]
        else:
            return self.data[group]
    def setData(self, group, key, value):
        if not group in self.data or not key in self.data[group]:
            return False
        self.data[group][key] = value
        return True
    def mergeData(self, data, target=None):
        if target == None:
            target = self.data
        for key, value in data.items():
            if isinstance(value, dict):
                if not key in target:
                    target[key] = dict()
                target[key] = self.mergeData(value, target[key])
            elif isinstance(value, list):
                if not key in target:
                    target[key] = []
                target[key].extend(value)
            else:
                target[key] = value
        return target

    def getAudioBufferSize(self):
        return self.getData(256, "audio", "bufferSize")
    def getAudioRate(self):
        return self.getData(48000, "audio", "rate")
    def getAudioOutput(self):
        return self.getData("i2s", "audio", "output")
    def getAudioChannels(self):
        return 2
    def getAudioBits(self):
        return 16

    def getAudioVolume(self):
        return self.getData(1.0, "audio", "volume")
    def setAudioVolume(self, value):
        if value < 0 or value > 1:
            return False
        return self.setData("audio", "volume", value)

    def getMidiChannel(self):
        return self.getData(1, "midi", "channel")
    def setMidiChannel(self, value):
        if type(value) != type(1) or value < 1 or value > 16:
            return False
        return self.setData("midi", "channel", value)

    def getMidiThru(self):
        return self.getData(False, "midi", "thru")
    def setMidiThru(self, value):
        if type(value) != type(True):
            return False
        return self.setData("midi", "thru", value)
