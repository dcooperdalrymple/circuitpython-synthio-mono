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
        from rotaryio import IncrementalEncoder
        from adafruit_debouncer import Debouncer

        self._encoder.deinit()
        del self._encoder
        del self._button
        del self._button_pin
