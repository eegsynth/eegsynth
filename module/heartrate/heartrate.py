#!/usr/bin/env python

# Heartrate detects beats and returns the heart rate based on the beat-to-beat interval
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017-2018 EEGsynth project
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
import numpy as np
import os
import redis
import sys
import time
import threading

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import FieldTrip
import EEGsynth

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

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip','timeout')

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
    if (time.time()-start)>timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug>0:
    print "Data arrived"
if debug>1:
    print hdr_input
    print hdr_input.labels

channel   = patch.getint('input','channel')-1                                 # one-offset in the ini file, zero-offset in the code
window    = round(patch.getfloat('processing','window') * hdr_input.fSample)  # in samples
threshold = patch.getfloat('processing', 'threshold')
lrate     = patch.getfloat('processing', 'learning_rate')
debounce  = patch.getfloat('processing', 'debounce', default=0.3)             # minimum time between beats (s)
key_beat  = patch.getstring('output', 'heartbeat')
key_rate  = patch.getstring('output', 'heartrate')

curvemin  = np.nan;
curvemean = np.nan;
curvemax  = np.nan;
prev      = np.nan

begsample = -1
endsample = -1

while True:
    time.sleep(patch.getfloat('general','delay'))

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        print "Error: buffer reset detected"
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug>0:
            print "Waiting for data..."
        continue

    # process the last window
    begsample = hdr_input.nSamples - int(window)
    endsample = hdr_input.nSamples - 1
    dat       = ft_input.getData([begsample,endsample])[:,channel]

    if np.isnan(curvemin):
        curvemin  = np.min(dat)
        curvemean = np.mean(dat)
        curvemax  = np.max(dat)
    else:
        # the learning rate determines how fast the threshold auto-scales (0=never, 1=immediate)
        curvemin  = (1 - lrate) * curvemin  + lrate * np.min(dat)
        curvemean = (1 - lrate) * curvemean + lrate * np.mean(dat)
        curvemax  = (1 - lrate) * curvemax  + lrate * np.max(dat)

    # both are defined as positive
    negrange = curvemean - curvemin
    posrange = curvemax - curvemean

    if negrange>posrange:
        thresh = (curvemean - dat) > threshold * negrange
    else:
        thresh = (dat - curvemean) > threshold * posrange

    if not np.isnan(prev):
        prevsample = int(round(prev * hdr_input.fSample)) - begsample
        if prevsample>0 and prevsample<len(thresh):
            thresh[0:prevsample] = False

    # determine samples that are true and where the previous sample is false
    thresh = np.logical_and(thresh[1:], np.logical_not(thresh[0:-1]))
    sample = np.where(thresh)[0]+1

    if len(sample)<1:
        # no beat was detected
        continue

    # determine the last beat in the window
    last = sample[-1]
    last = (last + begsample) / hdr_input.fSample

    if np.isnan(prev):
        # the first beat has not been detected yet
        prev = last
        continue

    if last-prev>debounce:
        # require a minimum time between beats
        bpm  = 60./(last-prev)
        prev = last

        if not np.isnan(bpm):
            # this is to schedule a timer that switches the gate off
            duration        = patch.getfloat('general', 'duration', default=0.1)
            duration_scale  = patch.getfloat('scale', 'duration', default=1)
            duration_offset = patch.getfloat('offset', 'duration', default=0)
            duration        = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)

            patch.setvalue(key_rate, bpm, debug=debug)
            patch.setvalue(key_beat, bpm, debug=debug, duration=duration)
