# circuitpython-synthio-mono
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

import time, board, gc
from digitalio import DigitalInOut, Direction
from synthio_mono import *

# Initialize status LED
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

# Wait for USB to stabilize
time.sleep(0.5)

# Serial Header
print("circuitpython-synthio-mono")
print("Version 1.0")
print("Cooper Dalrymple, 2023")
print("https://dcdalrymple.com/circuitpython-synthio-mono/")

gc.collect()

print("\n:: Reading Configuration ::")
config = Config()

print("\n:: Initializing Display ::")
display = get_display(config)
display.set_title("circuitpython-synthio-mono v1.0")
display.set_value("Loading...")

print("\n:: Initializing Encoder ::")
encoder = Encoder(
    pin_a=config.gpio(("encoder", "a"), "GP12"),
    pin_b=config.gpio(("encoder", "b"), "GP13"),
    pin_button=config.gpio(("encoder", "btn"), "GP7")
)

print("\n:: Initializing Midi ::")
midi = Midi(
    uart_tx=config.gpio(("midi", "uart_tx")),
    uart_rx=config.gpio(("midi", "uart_rx"))
)

print("\n:: Initializing Audio ::")
audio = Audio(
    type=config.get(("audio", "type"), "i2s"),
    i2s_clk=config.gpio(("audio", "clk"), "GP0"),
    i2s_ws=config.gpio(("audio", "ws"), "GP1"),
    i2s_data=config.gpio(("audio", "data"), "GP2"),
    pwm_left=config.gpio(("audio", "pwm_left"), "GP0"),
    pwm_right=config.gpio(("audio", "pwm_right"), "GP1"),
    sample_rate=config.get(("audio", "rate"), 22050),
    buffer_size=config.get(("audio", "buffer"), 4096)
)

print("\n:: Initializing Synthio ::")
synth = Synth(audio)

print("\n:: Building Waveforms ::")
waveforms = Waveforms(
    samples=config.get(("waveform", "samples"), 256),
    amplitude=config.get(("waveform", "amplitude"), 12000)
)

print("\n:: Building Voice ::")
min_filter_frequency=config.get(("oscillator", "filter", "min_frequency"), 60.0)
max_filter_frequency=min(audio.get_sample_rate()*0.45, config.get(("oscillator", "filter", "max_frequency"), 20000.0))
voice = Voice(
    synth,
    waveforms,
    min_filter_frequency=min_filter_frequency,
    max_filter_frequency=max_filter_frequency
)

print("\n:: Managing Keyboard ::")
keyboard = Keyboard()
arpeggiator = Arpeggiator()
keyboard.set_arpeggiator(arpeggiator)

def press(note, velocity):
    voice.press(note, velocity)
keyboard.set_press(press)
arpeggiator.set_press(press)

def release():
    voice.release()
keyboard.set_release(release)
arpeggiator.set_release(release)

print("\n:: Routing Parameters ::")
parameters = Parameters()
patches = Patches(parameters)

parameters.add_groups([
    ParameterGroup("global", "Global"),
    ParameterGroup("arp", "Arp"),
    ParameterGroup("voice", "Voice"),
    ParameterGroup("osc0", "Osc 1"),
    ParameterGroup("osc1", "Osc 2"),
])

parameters.add_parameters([

    # Global
    Parameter(
        name="patch",
        label="Patch",
        group="global",
        range=patches.get_list(),
        set_callback=patches.read,
        mod=False,
        patch=False
    ),
    Parameter(
        name="midi_channel",
        label="MIDI Channel",
        group="global",
        range=(config.get(("midi", "min_channel"), 0), config.get(("midi", "max_channel"), 15)),
        set_callback=midi.set_channel,
        mod=False,
        patch=False
    ),
    Parameter(
        name="midi_thru",
        label="MIDI Thru",
        group="global",
        range=True,
        set_callback=midi.set_thru,
        mod=False,
        patch=False
    ),
    Parameter(
        name="volume",
        label="Volume",
        group="global",
        value=1.0,
        set_callback=audio.set_level
    ),
    Parameter(
        name="glide",
        label="Glide",
        group="global",
        range=(config.get(("oscillator", "min_glide"), 0.05), config.get(("oscillator", "max_glide"), 2.0)),
        set_callback=voice.set_glide,
        patch=False
    ),
    Parameter(
        name="keyboard_type",
        label="Note Type",
        group="global",
        range=keyboard.get_types(),
        set_callback=keyboard.set_type
    ),
    Parameter(
        name="velocity_amount",
        label="Velocity Amount",
        group="global",
        set_callback=voice.set_velocity_amount
    ),
    Parameter(
        name="bend_amount",
        label="Bend Amount",
        group="global",
        range=config.get(("oscillator", "max_bend"), 1.0),
        value=1.0,
        set_callback=voice.set_pitch_bend_amount,
        patch=False
    ),
    Parameter(
        name="mod_parameter",
        label="Mod Wheel",
        group="global",
        set_callback=parameters.set_mod_parameter,
        mod=False
    ),

    # Arpeggiator
    Parameter(
        name="arp_enabled",
        label="Arpeggiator",
        group="arp",
        range=True,
        set_callback=arpeggiator.set_enabled,
        set_argument=keyboard # Allows the notes to be updated
    ),
    Parameter(
        name="arp_type",
        label="Type",
        group="arp",
        range=arpeggiator.get_types(),
        set_callback=arpeggiator.set_type
    ),
    Parameter(
        name="arp_octaves",
        label="Octaves",
        group="arp",
        range=3,
        value=0.5,
        set_callback=arpeggiator.set_octaves
    ),
    Parameter(
        name="arp_bpm",
        label="BPM",
        group="arp",
        range=(config.get(("arpeggiator", "min_bpm"), 60), config.get(("arpeggiator", "max_bpm"), 240)),
        set_callback=arpeggiator.set_bpm
    ),
    Parameter(
        name="arp_steps",
        label="Steps Per Beat",
        group="arp",
        range=arpeggiator.get_step_options(),
        set_callback=arpeggiator.set_step_option
    ),
    Parameter(
        name="arp_gate",
        label="Gate",
        group="arp",
        range=(config.get(("arpeggiator", "min_gate"), 0.1), config.get(("arpeggiator", "max_gate"), 1.0)),
        value=1.0,
        set_callback=arpeggiator.set_gate
    ),

    # Voice
    Parameter(
        name="waveform",
        label="Waveform",
        group="voice",
        range=waveforms.get_list(),
        set_callback=voice.set_waveform
    ),
    Parameter(
        name="filter_type",
        label="Filter",
        group="voice",
        range=synth.get_filter_types(),
        set_callback=voice.set_filter_type
    ),
    Parameter(
        name="filter_frequency",
        label="Frequency",
        group="voice",
        range=(min_filter_frequency, max_filter_frequency),
        value=1.0,
        set_callback=voice.set_filter_frequency
    ),
    Parameter(
        name="filter_resonance",
        label="Resonace",
        group="voice",
        range=(config.get(("oscillator", "filter", "min_resonance"), 0.25), config.get(("oscillator", "filter", "max_resonance"), 16.0)),
        set_callback=voice.set_filter_resonance
    ),
    Parameter(
        name="filter_envelope_attack_time",
        label="Filter Env Attack",
        group="voice",
        range=(config.get(("oscillator", "envelope", "min_time"), 0.05), config.get(("oscillator", "envelope", "max_time"), 2.0)),
        set_callback=voice.set_filter_attack_time
    ),
    Parameter(
        name="filter_envelope_release_time",
        label="Filter Env Release",
        group="voice",
        range=(config.get(("oscillator", "envelope", "min_time"), 0.05), config.get(("oscillator", "envelope", "max_time"), 2.0)),
        set_callback=voice.set_filter_release_time
    ),
    Parameter(
        name="filter_envelope_amount",
        label="Filter Env Amount",
        group="voice",
        range=(0.0, max_filter_frequency-min_filter_frequency),
        set_callback=voice.set_filter_amount
    ),
    Parameter(
        name="filter_lfo_rate",
        label="Filter Lfo Rate",
        group="voice",
        set_callback=voice.set_filter_lfo_rate
    ),
    Parameter(
        name="filter_lfo_depth",
        label="Filter Lfo Depth",
        group="voice",
        range=(0.0, (max_filter_frequency-min_filter_frequency)/2),
        set_callback=voice.set_filter_lfo_depth
    ),
    Parameter(
        name="pan",
        label="Pan",
        group="voice",
        range=1.0,
        value=0.5,
        set_callback=voice.set_pan,
        patch=False
    ),
    Parameter(
        name="attack_time",
        label="Attack Time",
        group="voice",
        range=(config.get(("oscillator", "envelope", "min_time"), 0.05), config.get(("oscillator", "envelope", "max_time"), 2.0)),
        set_callback=voice.set_envelope_attack_time
    ),
    Parameter(
        name="decay_time",
        label="Decay Time",
        group="voice",
        range=(config.get(("oscillator", "envelope", "min_time"), 0.05), config.get(("oscillator", "envelope", "max_time"), 2.0)),
        set_callback=voice.set_envelope_decay_time
    ),
    Parameter(
        name="release_time",
        label="Release Time",
        group="voice",
        range=(config.get(("oscillator", "envelope", "min_time"), 0.05), config.get(("oscillator", "envelope", "max_time"), 2.0)),
        set_callback=voice.set_envelope_release_time
    ),
    Parameter(
        name="attack_level",
        label="Attack Level",
        group="voice",
        value=1.0,
        set_callback=voice.set_envelope_attack_level
    ),
    Parameter(
        name="sustain_level",
        label="Sustain Level",
        group="voice",
        value=1.0,
        set_callback=voice.set_envelope_sustain_level
    ),

    # Oscillator 1
    Parameter(
        name="glide_0",
        label="Glide",
        group="osc0",
        range=(config.get(("oscillator", "min_glide"), 0.05), config.get(("oscillator", "max_glide"), 2.0)),
        set_callback=voice.oscillators[0].set_glide
    ),
    Parameter(
        name="bend_amount_0",
        label="Bend Amount",
        group="osc0",
        range=config.get(("oscillator", "max_bend"), 1.0),
        value=1.0,
        set_callback=voice.oscillators[0].set_pitch_bend_amount
    ),
    Parameter(
        name="waveform_0",
        label="Waveform",
        group="osc0",
        range=waveforms.get_list(),
        set_callback=voice.oscillators[0].set_waveform
    ),
    Parameter(
        name="level_0",
        label="Level",
        group="osc0",
        value=1.0,
        set_callback=voice.oscillators[0].set_level
    ),
    Parameter(
        name="coarse_tune_0",
        label="Coarse Tune",
        group="osc0",
        range=config.get(("oscillator", "max_coarse_tune"), 2.0),
        value=0.5,
        set_callback=voice.oscillators[0].set_coarse_tune
    ),
    Parameter(
        name="fine_tune_0",
        label="Fine Tune",
        group="osc0",
        range=config.get(("oscillator", "max_fine_tune"), 0.0833),
        value=0.5,
        set_callback=voice.oscillators[0].set_fine_tune
    ),
    Parameter(
        name="tremolo_rate_0",
        label="Tremolo Rate",
        group="osc0",
        set_callback=voice.oscillators[0].set_tremolo_rate
    ),
    Parameter(
        name="tremolo_depth_0",
        label="Tremolo Depth",
        group="osc0",
        set_callback=voice.oscillators[0].set_tremolo_depth
    ),
    Parameter(
        name="vibrato_rate_0",
        label="Vibrato Rate",
        group="osc0",
        set_callback=voice.oscillators[0].set_vibrato_rate
    ),
    Parameter(
        name="vibrato_depth_0",
        label="Vibrato Depth",
        group="osc0",
        set_callback=voice.oscillators[0].set_vibrato_depth
    ),
    Parameter(
        name="pan_0",
        label="Pan",
        group="osc0",
        value=0.5,
        set_callback=voice.oscillators[0].set_pan
    ),
    Parameter(
        name="pan_rate_0",
        label="Panning Rate",
        group="osc0",
        set_callback=voice.oscillators[0].set_pan_rate
    ),
    Parameter(
        name="pan_depth_0",
        label="Panning Depth",
        group="osc0",
        set_callback=voice.oscillators[0].set_pan_depth
    ),

    # Oscillator 2
    Parameter(
        name="glide_1",
        label="Glide",
        group="osc1",
        range=(config.get(("oscillator", "min_glide"), 0.05), config.get(("oscillator", "max_glide"), 2.0)),
        set_callback=voice.oscillators[1].set_glide
    ),
    Parameter(
        name="bend_amount_1",
        label="Bend Amount",
        group="osc1",
        range=config.get(("oscillator", "max_bend"), 1.0),
        value=1.0,
        set_callback=voice.oscillators[1].set_pitch_bend_amount
    ),
    Parameter(
        name="waveform_1",
        label="Waveform",
        group="osc1",
        range=waveforms.get_list(),
        set_callback=voice.oscillators[1].set_waveform
    ),
    Parameter(
        name="level_1",
        label="Level",
        group="osc1",
        value=0.0,
        set_callback=voice.oscillators[1].set_level
    ),
    Parameter(
        name="coarse_tune_1",
        label="Coarse Tune",
        group="osc1",
        range=config.get(("oscillator", "max_coarse_tune"), 2.0),
        value=0.5,
        set_callback=voice.oscillators[1].set_coarse_tune
    ),
    Parameter(
        name="fine_tune_1",
        label="Fine Tune",
        group="osc1",
        range=config.get(("oscillator", "max_fine_tune"), 0.0833),
        value=0.5,
        set_callback=voice.oscillators[1].set_fine_tune
    ),
    Parameter(
        name="tremolo_rate_1",
        label="Tremolo Rate",
        group="osc1",
        set_callback=voice.oscillators[1].set_tremolo_rate
    ),
    Parameter(
        name="tremolo_depth_1",
        label="Tremolo Depth",
        group="osc1",
        set_callback=voice.oscillators[1].set_tremolo_depth
    ),
    Parameter(
        name="vibrato_rate_1",
        label="Vibrato Rate",
        group="osc1",
        set_callback=voice.oscillators[1].set_vibrato_rate
    ),
    Parameter(
        name="vibrato_depth_1",
        label="Vibrato Depth",
        group="osc1",
        set_callback=voice.oscillators[1].set_vibrato_depth
    ),
    Parameter(
        name="pan_1",
        label="Pan",
        group="osc1",
        value=0.5,
        set_callback=voice.oscillators[1].set_pan
    ),
    Parameter(
        name="pan_rate_1",
        label="Panning Rate",
        group="osc1",
        set_callback=voice.oscillators[1].set_pan_rate
    ),
    Parameter(
        name="pan_depth_1",
        label="Panning Depth",
        group="osc1",
        set_callback=voice.oscillators[1].set_pan_depth
    )
])
parameters.get_parameter("mod_parameter").range = parameters.get_mod_parameters(True)
config.deinit()
gc.collect()

print("\n:: Loading Initial Patch ::")
patches.read_first()

print("\n:: Setting Up Menu ::")
menu = Menu(parameters, display, patches)
encoder.set_increment(menu.increment)
encoder.set_decrement(menu.decrement)
encoder.set_click(menu.toggle_select)
encoder.set_long_press(menu.toggle_save)
encoder.set_double_click(menu.confirm_save)

print("\n:: Initialization Complete ::")
display.set_value("Ready!")

def note_on(notenum, velocity):
    keyboard.append(notenum, velocity)
midi.set_note_on(note_on)

def note_off(notenum):
    keyboard.remove(notenum)
midi.set_note_off(note_off)

def control_change(control, value):
    name = None
    if control == 1: # Mod Wheel
        name = parameters.get_mod_parameter()
    elif control == 64: # Sustain
        keyboard.set_sustain(value)
    else:
        name = midi.get_control_parameter(control)
    if name:
        parameter = parameters.get_parameter(name)
        if parameter:
            parameter.set(value)
            if control != 1:
                menu.display(name)
midi.set_control_change(control_change)

def pitch_bend(value):
    voice.set_pitch_bend(value)
midi.set_pitch_bend(pitch_bend)

midi.init()

while True:
    now = time.monotonic()
    voice.update()
    encoder.update()
    arpeggiator.update(now)
    midi.update(now)
    display.update(now)

print("\n:: Deinitializing ::")

menu.deinit()
del menu
patches.deinit()
del patches
parameters.deinit()
del parameters
arpeggiator.deinit()
del arpeggiator
keyboard.deinit()
del keyboard
voice.deinit()
del voice
waveforms.deinit()
del waveforms
synth.deinit()
del synth
audio.deinit()
del audio
midi.deinit()
del midi
encoder.deinit()
del encoder
display.deinit()
del display
led.value = False
del led
free_all_modules()

print("\n:: Process Ended ::")
