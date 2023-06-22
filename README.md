# CircuitPython synthio Monophonic Synthesizer
Demonstration of CircuitPython's synthio module using the RP2040, hardware MIDI input, I2S audio output, and a 4x4 neotrellis module.

## Features

* Maximum 12 notes simultaneously (depending on settings).
* Multiple supported audio sample rates. Ie: 22050, 36000, 44100, 48000.
* Uses built-in flash memory of Pico and supports external SD card for configuration.
* Hardware midi uart with thru support.
* JSON system and patch configuration.
* I2S or PWM audio hardware options.
* Simple OLED display and rotary control.

## Requirements

* CircuitPython 8.2.0-beta.1 or greater
* adafruit_midi CircuitPython library

## Hardware

* [Raspberry Pi Pico using RP2040](https://www.raspberrypi.com/products/raspberry-pi-pico/)
* I2S Audio Module (optional), PCM5102A based device recommended
* SSD1306 128x64 OLED display
* KY-040 rotary encoder

## Software Installation

1. Download and install CircuitPython bootloader: [instructions & UF2 file](https://circuitpython.org/board/raspberry_pi_pico/).
2. Add adafruit_midi library to `/lib/adafruit_midi` in CircuitPython storage: [GitHub Repository](https://github.com/adafruit/Adafruit_CircuitPython_MIDI).
3. Copy `code.py`, `config.json`, and `default` folder of samples into root directory of CircuitPython storage.

## Configuration

All of the settings of the device and patches are configured using the config.json file stored in the root directory of CircuitPython. If you're not familiar with JSON, it's structure can be very strict and cause errors if it's not formatted properly. I recommending reading up on it [here](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON).

The first patch located in the `"patches"` array is loaded by default when the Pico boots up. You can add more patches here following the same format as the "Default" patch which will be loaded sequentially.
