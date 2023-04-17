#!/usr/bin/env python

# Audio2ft reads data from an audio device and writes it to a FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2022 EEGsynth project
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
import FieldTrip


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
    global ft_host, ft_port, ft_output, device, rate, blocksize, nchans, p, info, i, devinfo, stream, startfeedback, countfeedback

    try:
        ft_host = patch.getstring("fieldtrip", "hostname")
        ft_port = patch.getint("fieldtrip", "port")
        monitor.success("Trying to connect to buffer on %s:%i ..." % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.success("Connected to output FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")

    # get the options from the configuration file
    device = patch.getint("audio", "device")
    rate = patch.getint("audio", "rate", default=44100)
    blocksize = patch.getint("audio", "blocksize", default=1024)
    nchans = patch.getint("audio", "nchans", default=2)

    monitor.info("rate = %g" % rate)
    monitor.info("nchans = %g" % nchans)
    monitor.info("blocksize = %g" % blocksize)

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
    devinfo = p.get_device_info_by_index(device)
    monitor.info("Selected device is " + devinfo["name"])
    monitor.info(devinfo)
    monitor.info("------------------------------------------------------------------")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=nchans,
        rate=rate,
        input=True,
        input_device_index=device,
        frames_per_buffer=blocksize,
    )

    ft_output.putHeader(nchans, float(rate), FieldTrip.DATATYPE_INT16)

    startfeedback = time.time()
    countfeedback = 0

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global patch, name, path, monitor
    global ft_host, ft_port, ft_output, device, rate, blocksize, nchans, p, info, i, devinfo, stream, startfeedback, countfeedback
    global start, data

    # measure the time that it takes
    start = time.time()

    # read a block of data from the audio device
    data = stream.read(blocksize)

    # convert raw buffer to numpy array and write to output buffer
    data = np.reshape(np.frombuffer(data, dtype=np.int16), (blocksize, nchans))
    ft_output.putData(data)

    monitor.trace("streamed " + str(blocksize) + " samples in " + str((time.time() - start) * 1000) + " ms")

    countfeedback += blocksize
    if countfeedback >= rate:
        # this gets printed approximately once per second
        monitor.debug("streamed " + str(countfeedback) + " samples in " + str((time.time() - startfeedback) * 1000) + " ms")
        startfeedback = time.time()
        countfeedback = 0

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


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
    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
