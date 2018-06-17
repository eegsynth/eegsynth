#!/usr/bin/env python

# Heartrate computes the heart rate based on the beat-to-beat interval
#
# Heartrate is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

# this is to prevent two threads accesing a variable at the same time
lock = threading.Lock()

def SetChannel(key, val):
    if debug > 1:
        print key, val
    lock.acquire()
    r.set(key, val)      # set it as control channel
    lock.release()

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
        curvemin  = curvemin  * (1-lrate) + lrate * np.min(dat)
        curvemean = curvemean * (1-lrate) + lrate * np.mean(dat)
        curvemax  = curvemax  * (1-lrate) + lrate * np.max(dat)

    # both are defined as positive
    negrange = curvemean-curvemin
    posrange = curvemax-curvemean

    if negrange>posrange:
        thresh = (curvemean - dat) > threshold * negrange
    else:
        thresh = (dat - curvemean) > threshold * posrange

    if not np.isnan(prev):
        prevsample = int(round(prev*hdr_input.fSample)) - begsample
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

        if debug>0:
            print key_rate, bpm

        if not np.isnan(bpm):
            r.publish(key_rate, bpm)  # send it as trigger
            r.publish(key_beat, bpm)  # send it as trigger
            SetChannel(key_rate, bpm) # set it as continuous control channel
            SetChannel(key_beat, 1)   # set it as binary control channel

            # schedule a timer to switch the binary control channel off
            duration = patch.getfloat('general', 'duration', default=0.1)
            duration_scale = patch.getfloat('scale', 'duration', default=1)
            duration_offset = patch.getfloat('offset', 'duration', default=0)
            duration = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)
            # some minimal time is needed for the delay
            duration = EEGsynth.limit(duration, 0.05, float('Inf'))
            t = threading.Timer(duration, SetChannel, args=[key_beat, 0])
            t.start()
