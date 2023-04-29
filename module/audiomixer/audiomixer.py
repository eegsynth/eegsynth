#!/usr/bin/env python

# Audiomixer reads data from a (virtual) audio device, mixes it, and writes it to another (virtual) audio device
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2022 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import os
import sys
import time
import pyaudio

if hasattr(sys, "frozen"):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == "__main__" and sys.argv[0] != "":
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == "__main__":
    path = os.path.abspath("")
    file = os.path.split(path)[-1] + ".py"
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, "../../lib"))
import EEGsynth


def update_mix():
    scale = patch.getfloat("scale", "mix", default=1.)
    offset = patch.getfloat("offset", "mix", default=0.)
    mix = np.zeros((input_nchans,output_nchans), dtype=float)
    for o in range(0,output_nchans):
        channame = "mix%d" % (o+1)
        chanmix = patch.getfloat("output", channame, multiple=True)
        for i in range(0,input_nchans):
            mix[i,o] = EEGsynth.rescale(chanmix[i], slope=scale, offset=offset)
    return mix


def _setup():
    """Initialize the module
    This adds a set of global variables
    """
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint("general", "debug", default=1))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    """Start the module
    This uses the global variables from setup and adds a set of global variables
    """
    global patch, name, path, monitor
    global delay, p, input_device, output_device, rate, blocksize, input_nchans, output_nchans, input_stream, output_stream, mix, previous

    # get the options from the configuration file
    delay = patch.getfloat("general", "delay", default=0.05)
    input_device = patch.getint("input", "device")
    input_nchans = patch.getint("input", "nchans", default=2)
    rate = patch.getint("input", "rate", default=44100)
    blocksize = patch.getint("input", "blocksize", default=1024)
    output_device = patch.getint("output", "device")
    output_nchans = patch.getint("output", "nchans", default=2)

    p = pyaudio.PyAudio()

    monitor.info("------------------------------------------------------------------")
    info = p.get_host_api_info_by_index(0)
    monitor.info(info)
    monitor.info("------------------------------------------------------------------")
    for i in range(info.get("deviceCount")):
        if p.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels") > 0:
            monitor.info("Input  Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get("name"))
        if (p.get_device_info_by_host_api_device_index(0, i).get("maxOutputChannels") > 0):
            monitor.info("Output Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get("name"))
    monitor.info("------------------------------------------------------------------")

    input_stream = p.open(
        format=pyaudio.paFloat32,
        channels=input_nchans,
        rate=rate,
        input=True,
        input_device_index=input_device,
        frames_per_buffer=blocksize,
        stream_callback=None
    )

    output_stream = p.open(
        format=pyaudio.paFloat32,
        channels=output_nchans,
        rate=rate,
        output=True,
        output_device_index=output_device,
        frames_per_buffer=blocksize,
        stream_callback=None
    )

    monitor.info("rate = %g" % rate)
    monitor.info("blocksize = %g" % blocksize)

    devinfo = p.get_device_info_by_index(input_device)
    monitor.info("input device = %s" % devinfo["name"])
    monitor.info("input nchans = %g" % input_nchans)

    devinfo = p.get_device_info_by_index(output_device)
    monitor.info("output device = %s" % devinfo["name"])
    monitor.info("output nchans = %g" % output_nchans)

    monitor.info("------------------------------------------------------------------")

    # construct the mixing matrix, it should be allowed to change over time
    mix = update_mix()
    previous = time.time()

    # there should not be any local variables in this function, they should all be global
    del info, i, devinfo
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global patch, name, path, monitor
    global delay, blocksize, input_stream, output_stream, mix, previous

    now = time.time()
    if (now-previous)>delay :
        # reconstruct the mixing matrix
        mix = update_mix()
        previous = now

    # read a block of data from the input audio device
    input_data = input_stream.read(blocksize, exception_on_overflow=False)

    # convert raw buffer to numpy array
    input_data = np.reshape(np.frombuffer(input_data, dtype=np.float32), (blocksize, input_nchans))

    # apply the mixing
    output_data = np.matmul(input_data, mix, dtype=np.float32)

    # convert numpy array to raw buffer
    output_data = output_data.tobytes()

    # write the block of data to the output audio device
    output_stream.write(output_data, exception_on_underflow=False)


def _loop_forever():
    """Run the main loop forever
    """
    global monitor
    while True:
        monitor.loop()
        _loop_once()


def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    """
    global stream, p
    input_stream.stop_stream()
    output_stream.stop_stream()
    input_stream.close()
    output_stream.close()
    p.terminate()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
