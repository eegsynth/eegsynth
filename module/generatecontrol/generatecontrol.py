#!/usr/bin/env python

# This module is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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
from scipy import signal

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

# the scale and offset are used to map Redis values to signal parameters
scale_frequency   = patch.getfloat('scale', 'frequency', default=1)
scale_amplitude   = patch.getfloat('scale', 'amplitude', default=1)
scale_offset      = patch.getfloat('scale', 'offset', default=1)
scale_noise       = patch.getfloat('scale', 'noise', default=1)
offset_frequency  = patch.getfloat('offset', 'frequency', default=0)
offset_amplitude  = patch.getfloat('offset', 'amplitude', default=0)
offset_offset     = patch.getfloat('offset', 'offset', default=0)
offset_noise      = patch.getfloat('offset', 'noise', default=0)
stepsize          = patch.getfloat('generate', 'stepsize') # in seconds

if debug > 1:
    print "update", update

prev_frequency = -1
prev_amplitude = -1
prev_offset    = -1
prev_noise     = -1

sample = 0

print "STARTING STREAM"
while True:

    # measure the time that it takes
    start = time.time();

    frequency = patch.getfloat('signal', 'frequency', default=1)
    amplitude = patch.getfloat('signal', 'amplitude', default=1)
    offset    = patch.getfloat('signal', 'offset', default=0)       # the DC component of the output
    noise     = patch.getfloat('signal', 'noise', default=0.5)
    # map the Redis values to signal parameters
    frequency = EEGsynth.rescale(frequency, slope=scale_frequency, offset=offset_frequency)
    amplitude = EEGsynth.rescale(amplitude, slope=scale_amplitude, offset=offset_amplitude)
    offset    = EEGsynth.rescale(offset, slope=scale_offset, offset=offset_offset)
    noise     = EEGsynth.rescale(noise, slope=scale_noise, offset=offset_noise)

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

    t = sample * update
    sample += 1

    key = patch.getstring('output', 'prefix') + '.sin'
    val = np.sin(2 * np.pi * frequency * t) * amplitude + offset + np.random.randn(1) * noise
    r.set(key, val[0])

    key = patch.getstring('output', 'prefix') + '.square'
    val = signal.square(2 * np.pi * frequency * t, 0.5) * amplitude + offset + np.random.randn(1) * noise
    r.set(key, val[0])

    key = patch.getstring('output', 'prefix') + '.triangle'
    val = signal.sawtooth(2 * np.pi * frequency * t, 0.5) * amplitude + offset + np.random.randn(1) * noise
    r.set(key, val[0])

    key = patch.getstring('output', 'prefix') + '.sawtooth'
    val = signal.sawtooth(2 * np.pi * frequency * t, 1) * amplitude + offset + np.random.randn(1) * noise
    r.set(key, val[0])

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = stepsize
    elapsed = time.time()-start
    naptime = desired - elapsed
    if naptime>0:
        # this approximates the real time streaming speed
        time.sleep(naptime)

    if debug>0:
        print "generated", sample, "samples in", (time.time()-start)*1000, "ms"
