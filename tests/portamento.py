# CircuitPython synthio Portamento with Single Shot LFO Example
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License

import board, time
import random, math
from audiobusio import I2SOut
from audiomixer import Mixer
import synthio
import ulab.numpy as numpy

I2S_CLK             = board.GP0
I2S_WS              = board.GP1
I2S_DATA            = board.GP2

SAMPLE_RATE         = 44100
BUFFER_SIZE         = 256
LEVEL               = 0.5

NOTE_ROOT           = 60 # C4
NOTE_RANGE          = 24
NOTE_SPEED          = 0.5
NOTE_UPDATE         = 2.0

WAVE_SAMPLES        = 256
WAVE_AMPLITUDE      = 12000 # out of 16384

# Waveform for lfo and oscillator: Basic Sine
waveform = numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, WAVE_SAMPLES, endpoint=False)) * WAVE_AMPLITUDE, dtype=numpy.int16)

# Setup I2S audio output and mixer to control buffer size and audio level
audio = I2SOut(I2S_CLK, I2S_WS, I2S_DATA)
mixer = Mixer(
    voice_count=1,
    sample_rate=SAMPLE_RATE,
    channel_count=2,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=BUFFER_SIZE
)
audio.play(mixer)
mixer.voice[0].level = LEVEL

# Generate our simple synthesizer object and attach it to the mixer
synth = synthio.Synthesizer(
    sample_rate=SAMPLE_RATE,
    channel_count=2
)
mixer.voice[0].play(synth)

# Single shot LFO to control interpolation between frequency
lerp_position = synthio.LFO(
    waveform=numpy.linspace(-16385, 16385, num=2, dtype=numpy.int16),
    rate=1/NOTE_SPEED,
    scale=1.0,
    offset=0.5,
    once=True
)
synth.blocks.append(lerp_position)

# Setup a math object to calculate the linear interpolation between "a" and "b" as controlled by "c" (the single shot position LFO)
lerp = synthio.Math(synthio.MathOperation.CONSTRAINED_LERP, 0.0, 0.0, lerp_position)
synth.blocks.append(lerp)

# Generate a simple vibrato LFO object
vibrato = synthio.LFO(
    waveform=waveform,
    rate=1.0,
    scale=0.1,
    offset=0.0
)
synth.blocks.append(vibrato)

# Setup another math object to add the interpolation and lfo values together for the final calculated bend value; None=0.0 (not used)
sum = synthio.Math(synthio.MathOperation.SUM, lerp, vibrato, None) # The 3rd input could be used for pitch bend
synth.blocks.append(sum)

# Construct a note object with the designated root frequency and have it always on
note = synthio.Note(
    waveform=waveform,
    frequency=synthio.midi_to_hz(NOTE_ROOT), # Root frequency
    bend=sum # Calculated frequency ratio per sample
)
synth.press(note)

while True:

    # Set start to last lerp position in case it is changed between glides
    lerp.a = lerp.value

    # Generate a random note within the designated range
    frequency = synthio.midi_to_hz(NOTE_ROOT+round(NOTE_RANGE*(random.random()*2-1)))

    # Set the desired end point as a relative octave of the root frequency using logarithmic functions
    lerp.b = math.log(frequency / note.frequency) / math.log(2)

    # Reset the position of the interpolation operation
    lerp_position.retrigger()

    time.sleep(NOTE_UPDATE)
