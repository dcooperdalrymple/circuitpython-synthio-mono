import time

class Midi:

    def __init__(self, uart=True, uart_tx=None, uart_rx=None, usb=False, ble=False, update=0.05, map_path="/midi.json"):
        self._thru = False
        self._note_on = None
        self._note_off = None
        self._control_change = None
        self._pitch_bend = None
        self._program_change = None
        self._update = update
        self._now = 0.0

        if uart:
            self._uart = UART(
                tx=uart_tx,
                rx=uart_rx,
                baudrate=31250,
                timeout=0.001
            )
            self._uart_midi = adafruit_midi.MIDI(
                midi_in=self._uart,
                midi_out=self._uart,
                in_channel=0,
                out_channel=0,
                debug=False
            )
        else:
            self._uart_midi = None

        if usb:
            import usb_midi
            self._usb_midi = adafruit_midi.MIDI(
                midi_in=usb_midi.ports[0],
                midi_out=usb_midi.ports[1],
                in_channel=0,
                out_channel=0,
                debug=False
            )
        else:
            self._usb_midi = None

        if ble:
            try:
                import adafruit_ble, adafruit_ble_midi
                from adafruit_ble.advertising.standard import ProvideServicesAdvertisement

                self._ble_midi_service = adafruit_ble_midi.MIDIService()
                self._ble_advertisement = ProvideServicesAdvertisement(self._ble_midi_service)

                self._ble = adafruit_ble.BLERadio()
                if self._ble.connected:
                    for connection in self._ble.connections:
                        connection.disconnect()

                self._ble_midi = adafruit_midi.MIDI(
                    midi_in=self._ble_midi_service,
                    midi_out=self._ble_midi_service,
                    in_channel=0,
                    out_channel=0,
                    debug=False
                )
            except Exception as e:
                self._ble_midi_service = None
                self._ble_advertisement = None
                self._ble = None
                self._ble_midi = None
                print("Device not bluetooth capable:")
        else:
            self._ble = None
            self._ble_midi = None

        self._map = read_json(map_path)

    def set_note_on(self, callback):
        self._note_on = callback
    def set_note_off(self, callback):
        self._note_off = callback
    def set_control_change(self, callback):
        self._control_change = callback
    def set_pitch_bend(self, callback):
        self._pitch_bend = callback
    def set_program_change(self, callback):
        self._program_change = callback

    def init(self):
        if self._ble and self._ble_advertisement:
            self._ble.start_advertising(self._ble_advertisement)

    def set_channel(self, value):
        if self._uart_midi:
            self._uart_midi.in_channel = value
            self._uart_midi.out_channel = value
        if self._usb_midi:
            self._usb_midi.in_channel = value
            self._usb_midi.out_channel = value
        if self._ble_midi:
            self._ble_midi.in_channel = value
            self._ble_midi.out_channel = value
    def set_thru(self, value):
        self._thru = value

    def _process_message(self, msg):
        if not msg:
            return

        if isinstance(msg, NoteOn):
            if msg.velocity > 0.0:
                if self._note_on:
                    self._note_on(msg.note, msg.velocity / 127.0)
            elif self._note_off:
                self._note_off(msg.note)
        elif isinstance(msg, NoteOff):
            if self._note_off:
                self._note_off(msg.note)
        elif isinstance(msg, ControlChange):
            if self._control_change:
                self._control_change(msg.control, msg.value / 127.0)
        elif isinstance(msg, PitchBend):
            if self._pitch_bend:
                self._pitch_bend((msg.pitch_bend - 8192) / 8192)
        elif isinstance(msg, ProgramChange):
            if self._program_change:
                self._program_change(msg.patch)

        if self._thru:
            if self._uart_midi:
                self._uart_midi.send(msg)
            if self._usb_midi:
                self._usb_midi.send(msg)
            if self._ble and self._ble.connected and self._ble_midi:
                self._ble_midi.send(msg)
    def _process_messages(self, midi, limit=32):
        while limit>0:
            msg = midi.receive()
            if not msg:
                break
            self._process_message(msg)
            limit = limit - 1

    def get_control_parameter(self, control, default=None):
        return self._map.get(str(control), default)

    def update(self, now=None):
        if not now:
            now = time.monotonic()
        if now < self._now + self._update:
            return
        self._now = now

        if self._uart_midi:
            self._process_messages(self._uart_midi)
        if self._usb_midi:
            self._process_messages(self._usb_midi)
        if self._ble and self._ble.connected and self._ble_midi:
            self._process_messages(self._ble_midi)

    def deinit(self):
        del self._map
        if self._ble and self._ble.connected:
            for connection in self._ble.connections:
                connection.disconnect()
        if self._ble_midi:
            del self._ble_midi_service
            del self._ble_advertisement
            del self._ble
            del self._ble_midi
        if self._usb_midi:
            del self._usb_midi
        if self._uart_midi:
            del self._uart_midi
            del self._uart
