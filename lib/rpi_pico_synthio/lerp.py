"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: lerp.py
Title: Parameter Linear Interpolation
Version: 0.1.0
Since: 0.1.0
"""

class Lerp:
    def __init__(self, value, speed=0.25):
        self.current = value
        self.previous = value
        self.desired = value
        self.position = 0.0
        self.speed = speed
    def set(self, value):
        self.previous = self.current
        self.desired = value
        self.position = 0.0
    def get(self, update=False):
        if update:
            self.update()
        return self.current
    def setSpeed(self, value):
        if value > 0.0:
            self.speed = value
    def update(self):
        if self.position >= 1.0 and self.current != self.desired:
            self.current = self.desired
        elif self.position < 1.0:
            self.current = self.previous + self.position * (self.desired - self.previous)
            self.position = min(self.position + self.speed, 1.0)
