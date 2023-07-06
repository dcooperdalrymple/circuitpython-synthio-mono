# circuitpython-synthio-mono
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

from synthio_mono import free_module

# Disable write protection and unnecessary usb features
import storage, usb_hid, usb_cdc
storage.remount("/", False, disable_concurrent_write_protection=True)
usb_hid.disable()
usb_cdc.enable(console=True, data=False)
free_module((storage, usb_hid, usb_cdc))
del storage
del usb_hid
del usb_cdc

# Create directories
import os
def check_dir(path):
    try:
        os.stat(path)
    except:
        os.mkdir(path)
check_dir("/waveforms")
check_dir("/patches")

# Configure USB Midi
from synthio_mono import Config
import usb_midi
config = Config()
if config.get(("midi", "usb"), False):
    usb_midi.enable()
else:
    usb_midi.disable()
    free_module(usb_midi)
    del usb_midi

import gc
gc.collect()
