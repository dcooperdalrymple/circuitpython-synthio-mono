class Keyboard:
    def __init__(self):
        self._note_types = ["high", "low", "last"]
        self._notes = []
        self._type = 0
        self._sustain = False
        self._sustained = []
        self._press = None
        self._release = None

    def set_press(self, callback):
        self._press = callback
    def set_release(self, callback):
        self._release = callback

    def get_types(self):
        return self._note_types
    def get_type(self):
        return self._type
    def set_type(self, value):
        self._type = value

    def get_sustain(self):
        return self._sustain
    def set_sustain(self, value, update=True):
        value = map_boolean(value)
        if value != self._sustain:
            self._sustain = value
            self._sustained = []
            if self._sustain:
                self._sustained = self._notes.copy()
            if update:
                self._update()

    def _has_notes(self):
        if self._sustain and self._sustained:
            return True
        if self._notes:
            return True
        return False
    def _get_low(self):
        if not self._has_notes():
            return None
        selected = (127, 0)
        if self._notes:
            for note in self._notes:
                if note[0] < selected[0]:
                    selected = note
        if self._sustain and self._sustained:
            for note in self._sustained:
                if note[0] < selected[0]:
                    selected = note
        return selected
    def _get_high(self):
        if not self._has_notes():
            return None
        selected = (0, 0)
        if self._notes:
            for note in self._notes:
                if note[0] > selected[0]:
                    selected = note
        if self._sustain and self._sustained:
            for note in self._sustained:
                if note[0] > selected[0]:
                    selected = note
        return selected
    def _get_last(self):
        if self._sustain and self._sustained:
            return self._sustained[-1]
        if self._notes:
            return self._notes[-1]
        return None
    def get(self):
        type = self._note_types[self._type]
        if type == "high":
            return self._get_high()
        elif type == "low":
            return self._get_low()
        else: # "last"
            return self._get_last()

    def append(self, notenum, velocity, update=True):
        self.remove(notenum, False, True)
        note = (notenum, velocity)
        self._notes.append(note)
        if self._sustain:
            self._sustained.append(note)
        if update:
            self._update()
    def remove(self, notenum, update=True, remove_sustained=False):
        self._notes = [note for note in self._notes if note[0] != notenum]
        if remove_sustained and self._sustain and self._sustained:
            self._sustained = [note for note in self._sustained if note[0] != notenum]
        if update:
            self._update()

    def _update(self):
        note = self.get()
        if not note:
            if self._release:
                self._release()
        elif self._press:
            self._press(note[0], note[1])
