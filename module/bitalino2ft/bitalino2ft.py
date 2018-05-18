#!/usr/bin/env python

# Bitalino2ft reads data from a bitalino device and writes that data to a FieldTrip buffer
#
# This module is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
#
# Copyright (C) 2018 EEGsynth project
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
from bitalino import BITalino

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

device    = patch.getstring('bitalino', 'device')
fsample   = patch.getfloat('bitalino', 'fsample', default=1000)
blocksize = patch.getfloat('bitalino', 'blocksize', default=10)
channels  = patch.getint('bitalino', 'channels', multiple=True) # [0, 1, 2, 3, 4, 5]
nchans    = len(channels)
batterythreshold = patch.getint('bitalino', 'batterythreshold', default=30)

if debug > 0:
    print "fsample", fsample
    print "nchans", nchans
    print "blocksize", blocksize

datatype  = FieldTrip.DATATYPE_FLOAT32
ft_output.putHeader(nchans, float(fsample), datatype)

try:
    # Connect to BITalino
    device = BITalino(device)
    # Set battery threshold
    device.battery(batterythreshold)
    # Read BITalino version
    print(device.version())
    # Start Acquisition
    device.start(fsample, channels)
    # Turn BITalino led on
    digitalOutput = [1,1]
    device.trigger(digitalOutput)
except:
    print "Error: cannot connect to BITalino"
    exit()

print "STARTING STREAM"
while True:

    # measure the time that it takes
    start = time.time();

    dat = device.read(blocksize)
    # write the data to the output buffer
    ft_output.putData(dat.astype(np.float32))

    if debug>0:
        print "streamed", blocksize, "samples in", (time.time()-start)*1000, "ms"

# Stop acquisition
device.stop()

# Close connection
device.close()
