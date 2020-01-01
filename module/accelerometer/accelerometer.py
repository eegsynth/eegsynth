#!/usr/bin/env python

# Accelerometer records accelerometer data from OpenBCI board into FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2019 EEGsynth project
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
    raise RuntimeError('cannot connect to Redis server')

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug   = patch.getint('general', 'debug')
timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print("Waiting for data to arrive...")
    if (time.time() - start) > timeout:
        print("Error: timeout while waiting for data")
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.1)

if debug > 0:
    print("Data arrived")
if debug > 1:
    print(hdr_input)
    print(hdr_input.labels)

# get the processing arameters
window = patch.getfloat('processing', 'window')
window = int(window * hdr_input.fSample)  # expressed in samples

channel_items = config.items('input')
channel_name = []
channel_indx = []
for item in channel_items:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channel_name.append(item[0])                           # the channel name
    channel_indx.append(patch.getint('input', item[0]) - 1)  # the channel number

begsample = -1
endsample = -1

while True:
    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    hdr_input = ftc.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        print("Error: buffer reset detected")
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug > 0:
            print("Waiting for data...")
        continue

    # get the most recent data segment
    begsample = hdr_input.nSamples - int(window)
    endsample = hdr_input.nSamples - 1
    dat = ftc.getData([begsample, endsample]).astype(double)

    # this is for debugging
    printval = []

    for channame, chanindx in zip(channel_name, channel_indx):
        # compute the mean over the window
        key = patch.getstring('output', 'prefix') + '.' + channame
        val = np.mean(dat[:, chanindx])
        patch.setvalue(key, val)

        # this is for debugging
        printval.append(val)

    if debug > 1:
        print(printval)
