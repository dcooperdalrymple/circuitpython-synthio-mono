# Inspired by Arpy class from eighties_arp in https://github.com/todbot/circuitpython-synthio-tricks

class Arpeggiator:
    def __init__(self, bpm=120, steps=2):
        self._enabled = False
        self._gate = 0.3

        self._step_options = [
            {
                "steps": 0.5,
                "name": "half"
            },
            {
                "steps": 1.0,
                "name": "quarter"
            },
            {
                "steps": 1.5,
                "name": "dotted quarter"
            },
            {
                "steps": 2.0,
                "name": "eighth"
            },
            {
                "steps": 3.0,
                "name": "triplet"
            },
            {
                "steps": 4.0,
                "name": "sixteenth"
            },
            {
                "steps": 8.0,
                "name": "32nd"
            }
        ]
        self._update_timing(
            bpm=bpm,
            steps=steps
        )

        self._types = [
            "up",
            "down",
            "updown",
            "downup",
            "played",
            "random"
        ]
        self._type = 0
        self._octaves = 0

        self._raw_notes = []
        self._notes = []
        self._pos = 0
        self._now = time.monotonic()

        self._press = None
        self._release = None

    def _update_timing(self, bpm=None, steps=None):
        if bpm:
            self._bpm = bpm
        if steps:
            self._steps = steps
        self._step_time = 60.0 / self._bpm / self._steps
        self._gate_duration = self._gate * self._step_time
    def set_bpm(self, value):
        self._update_timing(bpm=value)
    def get_bpm(self):
        return self._bpm
    def set_steps(self, value):
        if type(value) is int:
            value = float(value)
        elif type(value) is dict:
            value = value.get("steps", 1)
        value = max(value, 0.01)
        self._update_timing(steps=value)
    def set_step_option(self, value):
        if not type(value) is int:
            self.set_steps(value)
        else:
            self.set_steps(self._step_options[value % len(self._step_options)])
    def get_steps(self):
        return self._steps
    def get_step_options(self):
        return self._step_options
    def set_gate(self, value):
        self._gate = value
        self._update_timing()
    def set_octaves(self, value):
        self._octaves = int(value)
        if self._notes:
            self.update_notes(self._raw_notes)

    def is_enabled(self):
        return self._enabled
    def set_enabled(self, value, keyboard=None):
        if value:
            self.enable(keyboard)
        else:
            self.disable()
    def enable(self, keyboard=None):
        self._enabled = True
        self._now = time.monotonic() - self._step_time
        if keyboard:
            self.update_notes(keyboard.get_notes())
    def disable(self, keyboard=None):
        self._enabled = False
        self.update_notes()
        if keyboard:
            keyboard.update()

    def set_press(self, callback):
        self._press = callback
    def set_release(self, callback):
        self._release = callback

    def get_types(self):
        return self._types
    def get_type(self, index=False):
        if index:
            return self._type
        else:
            return self._types[self._type]
    def set_type(self, value):
        if type(value) is int:
            self._type = value % len(self._types)
        elif type(value) is str:
            self._type = self._types.index(value)
        if self._notes:
            self.update_notes(self._raw_notes)

    def _get_notes(self, notes=[]):
        if not notes:
            return notes

        if abs(self._octaves) > 0:
            l = len(notes)
            for octave in range(1,abs(self._octaves)+1):
                if self._octaves < 0:
                    octave = octave * -1
                    for i in range(0,l):
                        notes.append((notes[i][0] + octave*12, notes[i][1]))

        type = self.get_type()
        if type == "up":
            notes.sort(key=lambda x: x[0])
        elif type == "down":
            notes.sort(key=lambda x: x[0], reverse=True)
        elif type == "updown":
            notes.sort(key=lambda x: x[0])
            if len(notes) > 2:
                _notes = notes[1:-1].copy()
                _notes.reverse()
                notes = notes + _notes
        elif type == "downup":
            notes.sort(key=lambda x: x[0], reverse=True)
            if len(notes) > 2:
                _notes = notes[1:-1].copy()
                _notes.reverse()
                notes = notes + _notes
        # "played" = notes stay as is, "random" = index is randomized on update

        return notes
    def update_notes(self, notes=[]):
        if not self._notes:
            self._pos = 0
            self._now = time.monotonic() - self._step_time
        self._raw_notes = notes.copy()
        self._notes = self._get_notes(notes)
        if not self._notes and self._release:
            self._release()

    def update(self, now=None):
        if not self._enabled or not self._notes:
            return

        if not now:
            now = time.monotonic()

        if now >= self._now + self._step_time:
            self._now = self._now + self._step_time
            if self.get_type() == "random":
                self._pos = random.randrange(0,len(self._notes),1)
            else:
                self._pos = (self._pos+1) % len(self._notes)
            if self._press:
                self._press(self._notes[self._pos][0], self._notes[self._pos][1])

        if now - self._now > self._gate_duration:
            if self._release:
                self._release()

    def deinit(self):
        del self._step_options
        del self._types
        del self._raw_notes
        del self._notes
