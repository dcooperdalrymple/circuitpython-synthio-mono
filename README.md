# CircuitPython synthio Monophonic Synthesizer
Parametric monophonic synthesizer built using CircuitPython's synthio module using the RP2040, UART/USB/BLE MIDI input, and I2S audio output. Controlled with a MIDI control interface or with a SSD1306-based 128x32 OLED and momentary switch rotary encoder.

[![Demonstration Video Thumbnail](assets/thumb.jpg)](https://www.youtube.com/watch?v=uuqIeZu2VT8 "Watch a demonstration of this project on YouTube")

## Features

* Single dual oscillator monophonic voice.
* Store patches and custom waveforms in onboard memory.
* Supports simultaneous USB, hardware (UART), and bluetooth (BLE) MIDI communication with global thru support.
* Simple OLED display and rotary control.
* Individual oscillator control of level, glide, tuning, pitch bend, waveform, tremolo, vibrato, and stereo panning.
* Global filter with three modes: Low-Pass, High-Pass, and Band-Pass.
* Configurable MIDI map.

## Requirements

* CircuitPython 8.2.0-beta.1 or greater
* All CircuitPython libraries provided

## Hardware

* [Raspberry Pi Pico W using RP2040](https://www.raspberrypi.com/products/raspberry-pi-pico/) or other compatible CircuitPython device with optional bluetooth support.
* I2S Audio Module, PCM5102A based device recommended
* SSD1306 128x32 OLED display
* KY-040 rotary encoder (or other rotary encoder with momentary switch)

## Software Compilation and Device Upload

### Linux

1. Download and install CircuitPython bootloader: [instructions & UF2 file](https://circuitpython.org/board/raspberry_pi_pico/).
2. Ensure that your device is connected and mounted as CIRCUITPYTHON and run the provided Makefile: `make` (the `--always-make` argument may be necessary to ensure that all files are forcibly uploaded to the device).

## Hardware Installation

_Coming soon..._
