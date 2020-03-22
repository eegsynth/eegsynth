#!/usr/bin/env python

# Bitalino2ft reads data from a bitalino device and writes that data to a FieldTrip buffer
#
# This module is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
#
# Copyright (C) 2018-2020 EEGsynth project
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
from bitalino import BITalino

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
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth
import FieldTrip

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
debug       = patch.getint('general', 'debug')
device      = patch.getstring('bitalino', 'device')
fsample     = patch.getfloat('bitalino', 'fsample', default=1000)
blocksize   = patch.getint('bitalino', 'blocksize', default=10)
channels    = patch.getint('bitalino', 'channels', multiple=True)  # these should be one-offset
batterythreshold = patch.getint('bitalino', 'batterythreshold', default=30)

# switch from one-offset to zero-offset
nchans = len(channels)
for i in range(nchans):
    channels[i] -= 1

monitor.info("fsample = " + str(fsample))
monitor.info("channels = " + str(channels))
monitor.info("nchans = " + str(nchans))
monitor.info("blocksize = " + str(blocksize))

try:
    ft_host = patch.getstring('fieldtrip', 'hostname')
    ft_port = patch.getint('fieldtrip', 'port')
    monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
    ft_output = FieldTrip.Client()
    ft_output.connect(ft_host, ft_port)
    monitor.success('Connected to output FieldTrip buffer')
except:
    raise RuntimeError("cannot connect to output FieldTrip buffer")

datatype = FieldTrip.DATATYPE_FLOAT32
ft_output.putHeader(nchans, float(fsample), datatype)

try:
    # Connect to BITalino
    device = BITalino(device)
    monitor.success((device.version()))
except:
    raise RuntimeError("cannot connect to BITalino")

# Set battery threshold
device.battery(batterythreshold)

# Start Acquisition
device.start(fsample, channels)

# Turn BITalino led on
digitalOutput = [1, 1]
device.trigger(digitalOutput)

startfeedback = time.time()
countfeedback = 0

while True:
    monitor.loop()

    # measure the time that it takes
    start = time.time()

    # read the selected channels from the bitalino
    dat = device.read(blocksize)
    # it starts with 5 extra channels, the first is the sample number (running from 0 to 15), the next 4 seem to be binary
    dat = dat[:, 5:]
    # write the data to the output buffer
    ft_output.putData(dat.astype(np.float32))

    countfeedback += blocksize

    if debug > 1:
        monitor.print("streamed", blocksize, "samples in", (time.time() - start) * 1000, "ms")
    elif debug > 0 and countfeedback >= fsample:
        # this gets printed approximately once per second
        monitor.print("streamed", countfeedback, "samples in", (time.time() - startfeedback) * 1000, "ms")
        startfeedback = time.time()
        countfeedback = 0

# Stop acquisition
device.stop()

# Close connection
device.close()
