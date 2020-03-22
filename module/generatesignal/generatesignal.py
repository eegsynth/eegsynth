#!/usr/bin/env python

# Generatesignal creates user-defined signals and writes these to the FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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
from scipy import signal as sp

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth
import FieldTrip

def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_output

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
        response = r.client_list()
    except redis.ConnectionError:
        raise RuntimeError("cannot connect to Redis server")

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug = patch.getint('general','debug')

    try:
        ft_host = patch.getstring('fieldtrip','hostname')
        ft_port = patch.getint('fieldtrip','port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.success('Connected to output FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_output
    global nchannels, fsample, shape, scale_frequency, scale_amplitude, scale_offset, scale_noise, scale_dutycycle, offset_frequency, offset_amplitude, offset_offset, offset_noise, offset_dutycycle, blocksize, datatype, block, begsample, endsample, timevec, phasevec

    # get the options from the configuration file
    nchannels         = patch.getint('generate', 'nchannels')
    fsample           = patch.getfloat('generate', 'fsample')
    shape             = patch.getstring('signal', 'shape') # sin, square, triangle, sawtooth or dc

    # the scale and offset are used to map the Redis values to internal values
    scale_frequency   = patch.getfloat('scale', 'frequency', default=1)
    scale_amplitude   = patch.getfloat('scale', 'amplitude', default=1)
    scale_offset      = patch.getfloat('scale', 'offset', default=1)
    scale_noise       = patch.getfloat('scale', 'noise', default=1)
    scale_dutycycle   = patch.getfloat('scale', 'dutycycle', default=1)
    offset_frequency  = patch.getfloat('offset', 'frequency', default=0)
    offset_amplitude  = patch.getfloat('offset', 'amplitude', default=0)
    offset_offset     = patch.getfloat('offset', 'offset', default=0)
    offset_noise      = patch.getfloat('offset', 'noise', default=0)
    offset_dutycycle  = patch.getfloat('offset', 'dutycycle', default=0)

    blocksize = int(round(patch.getfloat('generate', 'window') * fsample))
    datatype  = 'float32'

    if datatype == 'uint8':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_UINT8)
    elif datatype == 'int8':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_INT8)
    elif datatype == 'uint16':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_UINT16)
    elif datatype == 'int16':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_INT16)
    elif datatype == 'uint32':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_UINT32)
    elif datatype == 'int32':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_INT32)
    elif datatype == 'float32':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_FLOAT32)
    elif datatype == 'float64':
        ft_output.putHeader(nchannels, fsample, FieldTrip.DATATYPE_FLOAT64)

    monitor.debug("nchannels", nchannels)
    monitor.debug("fsample", fsample)
    monitor.debug("blocksize", blocksize)

    block     = 0
    begsample = 0
    endsample = blocksize-1

    # the time axis per block remains the same, the phase linearly increases
    timevec  = np.arange(1, blocksize+1) / fsample
    phasevec = np.zeros(1)


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_output
    global nchannels, fsample, shape, scale_frequency, scale_amplitude, scale_offset, scale_noise, scale_dutycycle, offset_frequency, offset_amplitude, offset_offset, offset_noise, offset_dutycycle, blocksize, datatype, block, begsample, endsample, timevec, phasevec
    global start, frequency, amplitude, offset, noise, dutycycle, signal, dat_output, chan, desired, elapsed, naptime

    monitor.loop()

    if patch.getint('signal', 'rewind', default=0):
        monitor.info("Rewind pressed, jumping back to start of signal")
        # the sample number and phase should be 0 upon the start of the signal
        sample = 0
        phase = 0

    if not patch.getint('signal', 'play', default=1):
        monitor.info("Stopped")
        time.sleep(0.1);
        # the sample number and phase should be 0 upon the start of the signal
        sample = 0
        phase = 0
        return

    if patch.getint('signal', 'pause', default=0):
        monitor.info("Paused")
        time.sleep(0.1);
        return

    # measure the time to correct for the slip
    start = time.time();

    monitor.debug("Generating block", block, 'from', begsample, 'to', endsample)

    frequency = patch.getfloat('signal', 'frequency', default=10)
    amplitude = patch.getfloat('signal', 'amplitude', default=0.8)
    offset    = patch.getfloat('signal', 'offset', default=0)           # the DC component of the output signal
    noise     = patch.getfloat('signal', 'noise', default=0.1)
    dutycycle = patch.getfloat('signal', 'dutycycle', default=0.5)      # for the square wave

    # map the Redis values to signal parameters
    frequency = EEGsynth.rescale(frequency, slope=scale_frequency, offset=offset_frequency)
    amplitude = EEGsynth.rescale(amplitude, slope=scale_amplitude, offset=offset_amplitude)
    offset    = EEGsynth.rescale(offset, slope=scale_offset, offset=offset_offset)
    noise     = EEGsynth.rescale(noise, slope=scale_noise, offset=offset_noise)
    dutycycle = EEGsynth.rescale(dutycycle, slope=scale_dutycycle, offset=offset_dutycycle)

    monitor.update("frequency", frequency)
    monitor.update("amplitude", amplitude)
    monitor.update("offset   ", offset)
    monitor.update("noise    ", noise)
    monitor.update("dutycycle", dutycycle)

    # compute the phase of each sample in this block
    phasevec = 2 * np.pi * frequency * timevec + phasevec[-1]
    if shape=='sin':
        signal = np.sin(phasevec) * amplitude + offset
    elif shape=='square':
        signal = sp.square(phasevec, dutycycle) * amplitude + offset
    elif shape=='triangle':
        signal = sp.sawtooth(phasevec, 0.5) * amplitude + offset
    elif shape=='sawtooth':
        signal = sp.sawtooth(phasevec, 1) * amplitude + offset
    elif shape=='dc':
        signal = phasevec * 0. + offset

    dat_output = np.random.randn(blocksize, nchannels) * noise
    for chan in range(nchannels):
        dat_output[:,chan] += signal

    # write the data to the output buffer
    if datatype == 'uint8':
        ft_output.putData(dat_output.astype(np.uint8))
    elif datatype == 'int8':
        ft_output.putData(dat_output.astype(np.int8))
    elif datatype == 'uint16':
        ft_output.putData(dat_output.astype(np.uint16))
    elif datatype == 'int16':
        ft_output.putData(dat_output.astype(np.int16))
    elif datatype == 'uint32':
        ft_output.putData(dat_output.astype(np.uint32))
    elif datatype == 'int32':
        ft_output.putData(dat_output.astype(np.int32))
    elif datatype == 'float32':
        ft_output.putData(dat_output.astype(np.float32))
    elif datatype == 'float64':
        ft_output.putData(dat_output.astype(np.float64))

    begsample += blocksize
    endsample += blocksize
    block += 1

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = blocksize/fsample
    elapsed = time.time()-start
    naptime = desired - elapsed
    if naptime>0:
        # this approximates the real time streaming speed
        time.sleep(naptime)

    monitor.info("generated " + str(blocksize) + " samples in " + str((time.time() - start) * 1000) + " ms")



def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, ft_output

    ft_output.disconnect()
    monitor.success('Disconnected from output FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
