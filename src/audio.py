from audiomixer import Mixer
import synthio

class Audio:

    def __init__(self, type="i2s", i2s_clk=None, i2s_ws=None, i2s_data=None, pwm_left=None, pwm_right=None, sample_rate=22050, buffer_size=1024):
        if type == "i2s":
            from audiobusio import I2SOut
            self._output = I2SOut(
                bit_clock=i2s_clk,
                word_select=i2s_ws,
                data=i2s_data
            )
        else: # "pwm"
            from audiopwmio import PWMAudioOut
            self._output = PWMAudioOut(
                left_channel=pwm_left,
                right_channel=pwm_right
            )

        self._mixer = Mixer(
            voice_count=1,
            sample_rate=sample_rate,
            channel_count=2,
            bits_per_sample=16,
            samples_signed=True,
            buffer_size=buffer_size
        )
        self._output.play(self._mixer)

    def get_sample_rate(self):
        return self._mixer.sample_rate
    def get_buffer_size(self):
        return self._mixer.buffer_size

    def set_level(self, value):
        self._mixer.voice[0].level = value

    def play(self, source):
        self._mixer.voice[0].play(source)

    def deinit(self):
        self._mixer.deinit()
        self._output.deinit()
