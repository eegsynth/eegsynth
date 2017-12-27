#!/usr/bin/env python

# Generatesignal generates user-defined sinewaves in the FieldTrip buffer
#
# Generatesignal is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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
debug = config.getint('general','debug')

try:
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
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
nchannels = config.getint('generate', 'nchannels')
fsample   = config.getfloat('generate', 'fsample')
blocksize = int(round(config.getfloat('generate', 'window') * fsample))

ft_output.putHeader(nchannels, fsample, datatype)

if debug > 1:
    print "nchannels", nchannels
    print "fsample", fsample
    print "blocksize", blocksize

scale_frequency   = config.getfloat('scale', 'frequency')
scale_amplitude   = config.getfloat('scale', 'amplitude')
scale_noise       = config.getfloat('scale', 'noise')

prev_frequency = -1
prev_amplitude = -1
prev_noise     = -1

begsample = 0
endsample = blocksize-1
block = 0

print "STARTING STREAM"
while True:

    # measure the time that it takes
    start = time.time();

    if debug>1:
        print "Generating block", block, 'from', begsample, 'to', endsample

    frequency = patch.getfloat('signal', 'frequency', default=10) * scale_frequency
    amplitude = patch.getfloat('signal', 'amplitude', default=1)  * scale_amplitude
    noise     = patch.getfloat('signal', 'noise', default=0.5)    * scale_noise

    if frequency != prev_frequency:
        print "frequency", frequency
        prev_frequency = frequency
    if amplitude != prev_amplitude:
        print "amplitude =", amplitude
        prev_amplitude = amplitude
    if noise != prev_noise:
        print "noise =", noise
        prev_noise = noise

    dat_output = np.random.randn(blocksize, nchannels) * noise
    signal = np.sin(2*np.pi*np.arange(begsample, endsample+1)*frequency/fsample) * amplitude
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
