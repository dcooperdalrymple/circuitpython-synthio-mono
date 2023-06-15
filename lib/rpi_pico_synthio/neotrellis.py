"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: neotrellis.py
Title: Neotrellis
Version: 0.1.0
Since: 0.1.0
"""

import time
import board
from busio import I2C
from adafruit_neotrellis.neotrellis import NeoTrellis as AdafruitNeoTrellis

class NeoTrellis:

    COLOR_BLACK = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_YELLOW = (255, 150, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_CYAN = (0, 255, 255)
    COLOR_BLUE = (0, 0, 255)
    COLOR_PURPLE = (180, 0, 255)
    COLOR_GRAY = (150, 150, 150)
    COLOR_WHITE = (255, 255, 255)

    COLOR_OFF = COLOR_BLACK
    COLOR_ACTIVATE = COLOR_PURPLE
    COLOR_DEFAULT = COLOR_RED
    COLOR_ACTIVE = COLOR_WHITE
    COLOR_MIDI = COLOR_GRAY

    def __init__(self, scl, sda, count=16, velocity=127):
        self.count = count
        self.velocity = velocity

        self.onEvent = False
        self.offEvent = False

        self.i2c = I2C(scl=scl, sda=sda)
        self.trellis = AdafruitNeoTrellis(self.i2c)
        self.buffer = [self.COLOR_OFF for i in range(self.count)]
        self.updatePixels()

    def activateAll(self, animate=True):
        for i in range(self.count):
            self.activateIndex(i)
            if animate:
                self.setPixel(i, self.COLOR_ACTIVATE, True)
                time.sleep(0.05)
        if animate:
            for i in range(self.count):
                self.setPixel(i, self.COLOR_OFF, True)
                time.sleep(0.05)

    def activateIndex(self, index):
        if index >= self.count or index < 0:
            return
        self.trellis.activate_key(index, AdafruitNeoTrellis.EDGE_RISING)
        self.trellis.activate_key(index, AdafruitNeoTrellis.EDGE_FALLING)
        self.trellis.callbacks[index] = self.handleTrellis

    def setPixel(self, index, color, update=True):
        if index >= self.count or index < 0:
            return
        if self.trellis.pixels[index] == self.buffer[index]:
            self.trellis.pixels[index] = color
        self.buffer[index] = color
        if update:
            self.trellis.pixels[index] = self.buffer[index]

    def fillPixels(self, color, update=True):
        for i in range(self.count):
            self.buffer[i] = color
        if update:
            self.updatePixels()

    def updatePixels(self):
        for i in range(self.count):
            self.trellis.pixels[i] = self.buffer[i]
            time.sleep(0.05)

    def getColor(self, name):
        name = name.lower()
        if name == "black":
            return self.COLOR_BLACK
        elif name == "red":
            return self.COLOR_RED
        elif name == "yellow":
            return self.COLOR_YELLOW
        elif name == "green":
            return self.COLOR_GREEN
        elif name == "cyan":
            return self.COLOR_CYAN
        elif name == "blue":
            return self.COLOR_BLUE
        elif name == "purple":
            return self.COLOR_PURPLE
        elif name == "gray":
            return self.COLOR_GRAY
        elif name == "white":
            return self.COLOR_WHITE
        else:
            return self.COLOR_DEFAULT

    def setOnEvent(self, callback):
        self.onEvent = callback
    def setOffEvent(self, callback):
        self.offEvent = callback

    def updateEvents(self):
        self.trellis.sync()

    def handleTrellis(self, event):
        # TODO: Change number to note and send velocity
        if event.edge == AdafruitNeoTrellis.EDGE_RISING:
            if self.onEvent:
                self.onEvent(event.number)
            self.trellis.pixels[event.number] = self.COLOR_ACTIVE
        elif event.edge == AdafruitNeoTrellis.EDGE_FALLING:
            if self.offEvent:
                self.offEvent(event.number)
            self.trellis.pixels[event.number] = self.buffer[event.number]
