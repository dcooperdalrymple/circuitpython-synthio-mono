class Encoder:

    def __init__(self, pin_a, pin_b, pin_button):
        self._encoder = IncrementalEncoder(pin_a, pin_b)
        self._position = None
        self._button_pin = DigitalInOut(pin_button)
        self._button_pin.direction = Direction.INPUT
        self._button_pin.pull = Pull.UP
        self._button = Button(self._button_pin, value_when_press=False)
        self._increment = None
        self._decrement = None
        self._press = None
        self._release = None
        self._long_press = None
        self._double_press = None

    def set_increment(self, callback):
        self._increment = callback
    def set_decrement(self, callback):
        self._decrement = callback
    def set_press(self, callback):
        self._press = callback
    def set_release(self, callback):
        self._release = callback
    def set_long_press(self, callback):
        self._long_press = callback
    def set_double_press(self, callback):
        self._double_press = callback

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
        if self._button.pressed:
            if self._button.short_count >= 2 and self._double_press:
                self._double_press()
            elif self._press:
                self._press()
        if self._button.long_press and self._long_press:
            self._long_press()
        if self._button.released and self._release:
            self._release()

    def deinit(self):
        from rotaryio import IncrementalEncoder
        from adafruit_debouncer import Debouncer

        self._encoder.deinit()
        del self._encoder
        del self._button
        del self._button_pin
