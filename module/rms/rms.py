#!/usr/bin/env python

# This module calculates a sliding-window RMS value of a signal
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

from nilearn import signal
import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import math
import multiprocessing
import numpy as np
import os
import redis
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout')

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time() - start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"
if debug > 1:
    print hdr_input
    print hdr_input.labels

channel_items = config.items('input')
channame = []
chanindx = []
for item in channel_items:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channame.append(item[0])                           # the channel name
    chanindx.append(patch.getint('input', item[0]) - 1)  # the channel number

prefix = patch.getstring('output', 'prefix')
window = patch.getfloat('processing', 'window')     # in seconds
window = round(window * hdr_input.fSample)          # in samples

begsample = -1
endsample = -1

while True:
    time.sleep(patch.getfloat('general', 'delay'))

    hdr_input = ftc.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        print "Error: buffer reset detected"
        raise SystemExit

    endsample = hdr_input.nSamples - 1
    if endsample < window:
        continue

    begsample = endsample - window + 1

    D = ftc.getData([begsample, endsample])
    D = D[:, chanindx]

    rms = [0.] * len(chanindx)
    for i, chanvec in enumerate(D.transpose()):
        for chanval in chanvec:
            rms[i] += chanval * chanval
        rms[i] = math.sqrt(rms[i] / len(chanvec))

    if debug > 0:
        print "rms =", rms

    for name, val in zip(channame, rms):
        # send it as control value: prefix.channelX=val
        key = "%s.%s" % (prefix, name)
        patch.setvalue(key, val)
