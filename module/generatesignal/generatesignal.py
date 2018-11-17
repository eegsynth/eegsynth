#!/usr/bin/env python

# Generatesignal creates user-defined signals and writes these to the FieldTrip buffer
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time
from scipy import signal as sp

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

try:
    ftc_host = patch.getstring('fieldtrip','hostname')
    ftc_port = patch.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
    exit()

datatype  = FieldTrip.DATATYPE_FLOAT32
nchannels = patch.getint('generate', 'nchannels')
fsample   = patch.getfloat('generate', 'fsample')
blocksize = int(round(patch.getfloat('generate', 'window') * fsample))

ft_output.putHeader(nchannels, fsample, datatype)

if debug > 1:
    print "nchannels", nchannels
    print "fsample", fsample
    print "blocksize", blocksize

# the scale and offset are used to map Redis values to signal parameters
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
shape             = patch.getstring('signal', 'shape') # sin, square, triangle or sawtooth

prev_frequency = -1
prev_amplitude = -1
prev_offset    = -1
prev_noise     = -1
prev_dutycycle = -1

block     = 0
begsample = 0
endsample = blocksize-1

# the time axis per block remains the same, the phase linearly increases
timevec  = np.arange(1, blocksize+1) / fsample
phasevec = np.zeros(1)

print "STARTING STREAM"
while True:

    if patch.getint('signal', 'rewind', default=0):
        if debug>0:
            print "Rewind pressed, jumping back to start of signal"
        # the sample number and phase should be 0 upon the start of the signal
        sample = 0
        phase = 0

    if not patch.getint('signal', 'play', default=1):
        if debug>0:
            print "Stopped"
        time.sleep(0.1);
        # the sample number and phase should be 0 upon the start of the signal
        sample = 0
        phase = 0
        continue

    if patch.getint('signal', 'pause', default=0):
        if debug>0:
            print "Paused"
        time.sleep(0.1);
        continue

    # measure the time that it takes
    start = time.time();

    if debug>1:
        print "Generating block", block, 'from', begsample, 'to', endsample

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

    if frequency!=prev_frequency or debug>2:
        print "frequency =", frequency
        prev_frequency = frequency
    if amplitude!=prev_amplitude or debug>2:
        print "amplitude =", amplitude
        prev_amplitude = amplitude
    if offset!=prev_offset or debug>2:
        print "offset    =", offset
        prev_offset = offset
    if noise!=prev_noise or debug>2:
        print "noise     =", noise
        prev_noise = noise
    if dutycycle!=prev_dutycycle or debug>2:
        print "dutycycle =", dutycycle
        prev_dutycycle = dutycycle

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

    dat_output = np.random.randn(blocksize, nchannels) * noise
    for chan in range(nchannels):
        dat_output[:,chan] += signal

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32))

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

    if debug>0:
        print "generated", blocksize, "samples in", (time.time()-start)*1000, "ms"
