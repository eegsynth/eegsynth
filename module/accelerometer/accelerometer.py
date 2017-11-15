#!/usr/bin/env python

# Accelerometer records accelerometer data from OpenBCI board into FieldTrip buffer
#
# Accelerometer is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

import ConfigParser
import argparse
import mne
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

# this determines how much debugging information gets printed
debug = config.getint('general','debug')
# this is the timeout for the FieldTrip buffer
timeout = config.getfloat('fieldtrip','timeout')

try:
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
    if (time.time()-start)>timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.2)

if debug>1:
    print hdr_input
    print hdr_input.labels

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# get the processing arameters
window = config.getfloat('processing','window')*hdr_input.fSample

channel_indx = []
channel_name = ['channelX', 'channelY', 'channelZ']
for chan in channel_name:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channel_indx.append(config.getint('input',chan)-1)

begsample = -1
endsample = -1

while True:
    time.sleep(config.getfloat('general','delay'))

    hdr_input = ftc.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        print "Error: buffer reset detected"
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug>0:
            print "Waiting for data..."
        continue

    # get the most recent data segment
    begsample = hdr_input.nSamples - int(window)
    endsample  = hdr_input.nSamples-1
    dat        = ftc.getData([begsample,endsample])

    # this is for debugging
    printval = []

    for chanstr,chanindx in zip(channel_name, channel_indx):

        # the scale option is channel specific
        if config.has_option('scale', chanstr):
            try:
                scale = config.getfloat('scale', chanstr)
            except:
                scale = r.get(config.get('scale', chanstr))
        else:
            scale = 1
        # the offset option is channel specific
        if config.has_option('offset', chanstr):
            try:
                offset = config.getfloat('offset', chanstr)
            except:
                offset = r.get(config.get('offset', chanstr))
        else:
            offset = 0

        # compute the mean over the window
        val = np.mean(dat[:,chanindx])

        # this is for debugging
        printval.append(val)

        # apply the scale and offset
        val = EEGsynth.rescale(val, scale, offset)

        # this is for debugging
        printval.append(val)

        r.set(config.get('output', 'prefix') + '.' + chanstr, val)

    if debug>1:
        print printval
