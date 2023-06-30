class Synth:
    def __init__(self, audio, min_filter_frequency=60.0, max_filter_frequency=20000.0):
        import synthio

        self._synth = synthio.Synthesizer(
            sample_rate=audio.get_sample_rate(),
            channel_count=2
        )
        audio.play(self._synth)

        self._min_filter_frequency = min_filter_frequency
        self._max_filter_frequency = max_filter_frequency
        self._filter_types = ["lpf", "hpf", "bpf"]

    def get_filter_types(self):
        return self._filter_types
    def build_filter(self, type, frequency, resonance):
        frequency = min(max(frequency, self._min_filter_frequency), self._max_filter_frequency)
        if type == "lpf":
            return self._synth.low_pass_filter(frequency, resonance)
        elif type == "hpf":
            return self._synth.high_pass_filter(frequency, resonance)
        else: # "bpf"
            return self._synth.band_pass_filter(frequency, resonance)

    def append(self, block):
        self._synth.blocks.append(block)
    def press(self, note):
        self._synth.press(note)
    def release(self, note):
        self._synth.release(note)

    def deinit(self):
        self._synth.release_all()
        self._synth.deinit()
