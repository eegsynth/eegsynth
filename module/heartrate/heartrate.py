#!/usr/bin/env python

# Heartrate detects beats and returns the heart rate based on the beat-to-beat interval
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
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

import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time
import threading

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
sys.path.insert(0, os.path.join(path,'../../lib'))
import FieldTrip
import EEGsynth

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
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug     = patch.getint('general','debug')
timeout   = patch.getfloat('fieldtrip','timeout', default=30)
channel   = patch.getint('input','channel')-1                                 # one-offset in the ini file, zero-offset in the code
window    = patch.getfloat('processing','window')
threshold = patch.getfloat('processing', 'threshold')
lrate     = patch.getfloat('processing', 'learning_rate', default=1)
debounce  = patch.getfloat('processing', 'debounce', default=0.3)             # minimum time between beats (s)
key_beat  = patch.getstring('output', 'heartbeat')
key_rate  = patch.getstring('output', 'heartrate')

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to input FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to input FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug>0:
        print("Waiting for data to arrive...")
    if (time.time()-start)>timeout:
        print("Error: timeout while waiting for data")
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.1)

if debug>0:
    print("Data arrived")
if debug>1:
    print(hdr_input)
    print(hdr_input.labels)

window = round(window * hdr_input.fSample)  # in samples

curvemin  = np.nan;
curvemean = np.nan;
curvemax  = np.nan;
prev      = np.nan

begsample = -1
endsample = -1

while True:
    monitor.loop()
    time.sleep(patch.getfloat('general','delay'))

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        print("Error: buffer reset detected")
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug>0:
            print("Waiting for data...")
        continue

    # process the last window
    begsample = hdr_input.nSamples - int(window)
    endsample = hdr_input.nSamples - 1
    dat       = ft_input.getData([begsample,endsample]).asdata(double)
    dat       = dat[:,channel]

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
