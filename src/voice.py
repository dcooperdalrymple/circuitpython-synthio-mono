

class LerpBlockInput:
    def __init__(self, synth, rate=0.05, value=0.0):
        self.position = synthio.LFO(
            waveform=numpy.linspace(-16385, 16385, num=2, dtype=numpy.int16),
            rate=1/rate,
            scale=1.0,
            offset=0.5,
            once=True
        )
        synth.append(self.position)
        self.lerp = synthio.Math(synthio.MathOperation.CONSTRAINED_LERP, value, value, self.position)
        synth.append(self.lerp)
    def get(self):
        return self.lerp
    def set(self, value):
        self.lerp.a = self.lerp.value
        self.lerp.b = value
        self.position.retrigger()
    def set_rate(self, value):
        self.position.rate = 1/value
    def get_rate(self):
        return self.position.rate

class Oscillator:
    def __init__(self, synth, waveforms, root=440.0):
        self._synth = synth
        self._waveforms = waveforms

        self.coarse_tune = 0.0
        self.fine_tune = 0.0
        self.bend_amount = 0.0
        self.bend = 0.0

        self.root = root
        self._log2 = math.log(2) # for octave conversion optimization
        self.frequency_lerp = LerpBlockInput(self._synth)
        self.vibrato = synthio.LFO(
            waveform=self._waveforms.get_data("sine"),
            rate=1.0,
            scale=0.0,
            offset=0.0
        )
        self.pitch_bend_lerp = LerpBlockInput(self._synth)
        self.note = synthio.Note(
            waveform=None,
            frequency=root,
            amplitude=synthio.LFO( # Tremolo
                waveform=self._waveforms.get_data("sine"),
                rate=1.0,
                scale=0.0,
                offset=1.0
            ),
            bend=synthio.Math(synthio.MathOperation.SUM, self.frequency_lerp.get(), self.vibrato, self.pitch_bend_lerp.get()),
            panning=synthio.LFO( # Panning
                waveform=self._waveforms.get_data("sine"),
                rate=1.0,
                scale=0.0,
                offset=0.0
            )
        )
        self._synth.append(self.note.amplitude)
        self._synth.append(self.note.bend)
        self._synth.append(self.note.panning)

    def set_frequency(self, value):
        self.frequency_lerp.set(math.log(value/self.root)/self._log2)
    def set_glide(self, value):
        self.frequency_lerp.set_rate(value)

    def set_pitch_bend_amount(self, value):
        self.bend_amount = value
        self._update_pitch_bend()
    def set_pitch_bend(self, value=None):
        self.bend = value
        self._update_pitch_bend()
    def _update_pitch_bend(self):
        self.pitch_bend_lerp.set(self.bend * self.bend_amount)

    def set_coarse_tune(self, value):
        self.coarse_tune = value
        self._update_root()
    def set_fine_tune(self, value):
        self.fine_tune = value
        self._update_root()
    def _update_root(self):
        self.note.frequency = self.root * pow(2,self.coarse_tune) * pow(2,self.fine_tune)

    def set_waveform(self, value):
        self.note.waveform = self._waveforms.get_data(value)

    def press(self):
        self._synth.press(self.note)
    def release(self):
        self._synth.release(self.note)

    def set_envelope(self, envelope):
        self.note.envelope = envelope
    def set_filter(self, filter):
        self.note.filter = filter

    def set_level(self, value):
        self.note.amplitude.offset = value
    def set_tremolo_rate(self, value):
        self.note.amplitude.rate = value
    def set_tremolo_depth(self, value):
        self.note.amplitude.scale = value
    def set_vibrato_rate(self, value):
        self.vibrato.rate = value
    def set_vibrato_depth(self, value):
        self.vibrato.scale = value
    def set_pan_rate(self, value):
        self.note.panning.rate = value
    def set_pan_depth(self, value):
        self.note.panning.scale = value
    def set_pan(self, value):
        self.note.panning.offset = value

class Voice:
    def __init__(self, synth, waveforms):
        self._synth = synth

        self.note = -1
        self.velocity = 0.0

        self.velocity_amount = 1.0
        self.attack_time = 0.0
        self.decay_time = 0.0
        self.release_time = 0.0
        self.attack_level = 1.0
        self.sustain_level = 0.75

        self.filter_type = 0
        self._filter_type = self.filter_type
        self.filter_frequency = 1.0
        self.filter_resonance = 0.0

        self.oscillators = (Oscillator(self._synth, waveforms), Oscillator(self._synth, waveforms))

    def press(self, note, velocity):
        self.velocity = velocity
        self._update_envelope()
        if note != self.note:
            frequency = synthio.midi_to_hz(note)
            for oscillator in self.oscillators:
                oscillator.set_frequency(frequency)
                oscillator.press()
    def release(self):
        for oscillator in self.oscillators:
            oscillator.release()
        self.note = -1

    def set_glide(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_glide(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_glide(value)

    def set_pitch_bend_amount(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_pitch_bend_amount(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_pitch_bend_amount(value)
    def set_pitch_bend(self, value):
        for oscillator in self.oscillators:
            oscillator.set_pitch_bend(value)

    def set_coarse_tune(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_coarse_tune(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_coarse_tune(value)
    def set_fine_tune(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_fine_tune(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_fine_tune(value)

    def set_waveform(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_waveform(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_waveform(value)

    def _update_filter(self):
        filter = self._synth.build_filter(self.get_filter_type(), self.get_filter_frequency(), self.get_filter_resonance())
        for oscillator in self.oscillators:
            oscillator.set_filter(filter)
    def get_filter_type(self):
        if type(self.filter_type) is int:
            return self._synth.get_filter_types()[self.filter_type]
        elif type(self.filter_type) is str:
            return self.filter_type
        else:
            return None
    def set_filter_type(self, value, update=True):
        self.filter_type = value
        if update and self.filter_type != self._filter_type:
            self._filter_type = self.filter_type
            self._update_filter()
    def set_filter_frequency(self, value, update=True):
        self.filter_frequency = value
        if update:
            self._update_filter()
    def get_filter_frequency(self):
        return self.filter_frequency
    def set_filter_resonance(self, value, update=True):
        self.filter_resonance = value
        if update:
            self._update_filter()
    def get_filter_resonance(self):
        return self.filter_resonance

    def _get_velocity_mod(self):
        return 1.0 - (1.0 - self.velocity) * self.velocity_amount
    def _build_envelope(self):
        mod = self._get_velocity_mod()
        return synthio.Envelope(
            attack_time=self.attack_time,
            decay_time=self.decay_time,
            release_time=self.release_time,
            attack_level=mod*self.attack_level,
            sustain_level=mod*self.sustain_level
        )
    def _update_envelope(self):
        envelope = self._build_envelope()
        for oscillator in self.oscillators:
            oscillator.set_envelope(envelope)
    def set_velocity_amount(self, value):
        self.velocity_amount = value
    def set_envelope_attack_time(self, value, update=True):
        self.attack_time = value
        if update:
            self._update_envelope()
    def get_envelope_attack_time(self):
        return self.attack_time
    def set_envelope_decay_time(self, value, update=True):
        self.decay_time = value
        if update:
            self._update_envelope()
    def get_envelope_decay_time(self):
        return self.decay_time
    def set_envelope_release_time(self, value, update=True):
        self.release_time = value
        if update:
            self._update_envelope()
    def get_envelope_release_time(self):
        return self.release_time
    def set_envelope_attack_level(self, value, update=True):
        self.attack_level = value
        if update:
            self._update_envelope()
    def get_envelope_attack_level(self):
        return self.attack_level
    def set_envelope_sustain_level(self, value, update=True):
        self.sustain_level = value
        if update:
            self._update_envelope()
    def get_envelope_sustain_level(self):
        return self.sustain_level

    def set_pan(self, value, index=None):
        if not index is None:
            self.oscillators[index].set_pan(value)
        else:
            for oscillator in self.oscillators:
                oscillator.set_pan(value)
