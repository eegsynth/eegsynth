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
blocksize = patch.getint('bitalino', 'blocksize', default=10)
channels  = patch.getint('bitalino', 'channels', multiple=True) # these should be one-offset
nchans    = len(channels)
batterythreshold = patch.getint('bitalino', 'batterythreshold', default=30)

if debug > 0:
    print "fsample", fsample
    print "channels", channels
    print "nchans", nchans
    print "blocksize", blocksize

# switch from one-offset to zero-offset
for i in range(nchans):
    channels[i]-=1;

datatype  = FieldTrip.DATATYPE_FLOAT32
ft_output.putHeader(nchans, float(fsample), datatype)

try:
    # Connect to BITalino
    device = BITalino(device)
except:
    print "Error: cannot connect to BITalino"
    exit()

# Read BITalino version
print(device.version())

# Set battery threshold
device.battery(batterythreshold)

# Start Acquisition
device.start(fsample, channels)

# Turn BITalino led on
digitalOutput = [1,1]
device.trigger(digitalOutput)

startfeedback = time.time()
countfeedback = 0

print "STARTING STREAM"
while True:

    # measure the time that it takes
    start = time.time();

    # read the selected channels from the bitalino
    dat = device.read(blocksize)
    # it starts with 5 extra channels, the first is the sample number (running from 0 to 15), the next 4 seem to be binary
    dat = dat[:,5:]
    # write the data to the output buffer
    ft_output.putData(dat.astype(np.float32))

    countfeedback += blocksize

    if debug>1:
        print "streamed", blocksize, "samples in", (time.time()-start)*1000, "ms"
    elif debug>0 and countfeedback>=fsample:
        # this gets printed approximately once per second
        print "streamed", countfeedback, "samples in", (time.time()-startfeedback)*1000, "ms"
        startfeedback = time.time();
        countfeedback = 0

# Stop acquisition
device.stop()

# Close connection
device.close()
