# circuitpython-synthio-mono
# 2023 Cooper Dalrymple - me@dcdalrymple.com
# GPL v3 License
# Version 1.0

# Disable write protection
import storage
storage.remount("/", False, True)

# Create directories
import os
def check_dir(path):
    try:
        os.stat(path)
    except:
        os.mkdir(path)
check_dir("/waveforms")
check_dir("/patches")
