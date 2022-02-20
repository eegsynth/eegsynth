#!/usr/bin/env python

# This module demodulates an audio signal that is comrised of a mixture of modulated tones
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

import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time
import pyaudio

if hasattr(sys, "frozen"):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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
    global parser, args, config, r, response, patch

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--inifile",
        default=os.path.join(path, name + ".ini"),
        help="name of the configuration file",
    )
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(
            host=config.get("redis", "hostname"),
            port=config.getint("redis", "port"),
            db=0,
            charset="utf-8",
            decode_responses=True,
        )
        response = r.client_list()
    except redis.ConnectionError:
        raise RuntimeError("cannot connect to Redis server")

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    """Start the module
    This uses the global variables from setup and adds a set of global variables
    """
    global parser, args, config, r, response, patch, name
    global monitor, debug, device, rate, blocksize, modulation, nchans, frequencies, ntones, scale_amplitude, offset_amplitude, scale_frequency, offset_frequency,key, p, info, i, devinfo, stream, startfeedback, countfeedback, offset

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint("general", "debug"))

    # get the options from the configuration file
    debug = patch.getint("general", "debug")
    device = patch.getint("audio", "device")
    rate = patch.getint("audio", "rate", default=44100)
    nchans = patch.getint("audio", "nchans", default=2)
    blocksize = patch.getint("audio", "blocksize", default=1024)
    modulation = patch.getstring('audio', 'modulation', default='am')
    frequencies = patch.getfloat('audio', 'frequencies', multiple=True)

    # these are for multiplying/attenuating the amplitude
    scale_amplitude = patch.getfloat('scale', 'amplitude', default=8)       # the default is for 8 controls
    offset_amplitude = patch.getfloat('offset', 'amplitude', default=0)
    scale_frequency = patch.getfloat('scale', 'frequency', default=0.1)     # the default is 100 Hz
    offset_frequency = patch.getfloat('offset', 'frequency', default=0)

    ntones = len(frequencies)
    offset = np.zeros((ntones, ), dtype=np.float32)

    monitor.info("rate       = %g" % rate)
    monitor.info("nchans     = %g" % nchans)
    monitor.info("blocksize  = %g" % blocksize)
    monitor.info("modulation = " + modulation)

    channame = ['left', 'right', 'chan3', 'chan4', 'chan5', 'chan6', 'chan7', 'chan8']
    key = []
    for chan in range(0, nchans):
        key.append([])
        for tone in range(0, ntones):
            tonestr = "tone%d" % (tone + 1)
            if patch.hasitem(channame[chan], tonestr):
                redischannel = patch.getstring(channame[chan], tonestr)
                key[chan].append(redischannel)
                monitor.info("configured " + channame[chan] + " " + tonestr + " as " + redischannel)
            else:
                key[chan].append(None)
                monitor.info("not configured " + channame[chan] + " " + tonestr)
                
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
        format=pyaudio.paFloat32,
        channels=nchans,
        rate=rate,
        input=True,
        input_device_index=device,
        frames_per_buffer=blocksize,
    )

    startfeedback = time.time()
    countfeedback = 0
    offset = 0.

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global parser, args, config, r, response, patch
    global rate, nchans, blocksize, frequencies, modulation, ntones, offset, startfeedback, countfeedback
    global start, data, chan, timeaxis, tone, phase, value, Fsin, Fcos, chanval

    # measure the time that it takes
    start = time.time()

    # read a block of data from the audio device and convert raw buffer to numpy array
    data = stream.read(blocksize)
    data = np.reshape(np.frombuffer(data, dtype=np.float32), (blocksize, nchans))

    timeaxis = np.arange(0, blocksize) / rate + offset
    freqaxis = np.arange(0,blocksize/2) * rate/blocksize
    offset += blocksize / rate

    for chan in range(0, nchans):
        if modulation == 'am':
            # the number of modulated tones is probably quite small, therefore
            # this uses a discrete Fourier transform for the demodulation
            for tone in range(0, ntones):
                if not key[chan][tone] == None:
                    phase = 2.0 * np.pi * frequencies[tone] * timeaxis
                    Fsin = np.dot(data[:, chan], np.sin(phase))
                    Fcos = np.dot(data[:, chan], np.cos(phase))
                    chanval = 2 * np.sqrt(Fsin*Fsin + Fcos*Fcos) / blocksize
                    chanval = EEGsynth.rescale(chanval, slope=scale_amplitude, offset=offset_amplitude)
                    patch.setvalue(key[chan][tone], chanval)
                    monitor.update(key[chan][tone], np.around(chanval,3)) # round to 3 decimals
        elif modulation == 'fm':
            F = np.abs(np.fft.fft(data[:, chan]))
            for tone in range(0, ntones):
                # determine the corresponding section of the amplitude spectrun
                if tone == ntones-1:
                    fmin = np.argmin(np.abs(freqaxis-frequencies[tone]))
                    fmax = round(blocksize/2) # search up to the Nyquist frequency
                else:
                    fmin = np.argmin(np.abs(freqaxis-frequencies[tone]))
                    fmax = np.argmin(np.abs(freqaxis-frequencies[tone+1])) # search up to the next tone
                # find the index of the maximum in the corresponding section of the amplitude spectrun
                fpeak = np.argmax(F[fmin:fmax]) # relative to the base frequency
                chanval = freqaxis[fpeak]
                chanval = EEGsynth.rescale(chanval, slope=scale_frequency, offset=offset_frequency)
                patch.setvalue(key[chan][tone], chanval)
                monitor.update(key[chan][tone], np.around(chanval,3)) # round to 3 decimals

    monitor.trace("streamed " + str(blocksize) + " samples in " + str((time.time() - start) * 1000) + " ms")

    countfeedback += blocksize
    if countfeedback >= rate:
        # this gets printed approximately once per second
        monitor.debug("streamed " + str(countfeedback) + " samples in " + str((time.time() - startfeedback) * 1000) + " ms")
        startfeedback = time.time()
        countfeedback = 0


def _loop_forever():
    """Run the main loop forever
    """
    global monitor
    while True:
        monitor.loop()
        _loop_once()


def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt
    """
    global stream, p
    stream.stop_stream()
    stream.close()
    p.terminate()
    sys.exit()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
