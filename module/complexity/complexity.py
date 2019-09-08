#!/usr/bin/env python

# Spectral outputs power envelopes of user-defined frequency bands
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
import math
import multiprocessing
import numpy as np
import os
import redis
import sys
import threading
import time
from neurokit.signal import complexity

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
elif sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
else:
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# get the options from the configuration file
debug = patch.getint('general','debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout')

try:
    ftc_host = patch.getstring('fieldtrip','hostname')
    ftc_port = patch.getint('fieldtrip','port')
    if debug>0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print("Connected to FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug>0:
        print("Waiting for data to arrive...")
    if (time.time()-start)>timeout:
        print("Error: timeout while waiting for data")
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.1)

if debug>0:
    print("Data arrived")
if debug>1:
    print(hdr_input)
    print(hdr_input.labels)

channel_items = config.items('input')
channame = []
chanindx = []
for item in channel_items:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channame.append(item[0])
    chanindx.append(patch.getint('input', item[0])-1)

if debug>0:
    print(channame, chanindx)

window      = patch.getfloat('processing','window')  # in seconds
window      = int(round(window * hdr_input.fSample)) # in samples
taper       = np.hanning(window)
frequency   = np.fft.rfftfreq(window, 1.0/hdr_input.fSample)
svd         = [True if patch.getint('metrics', 'svd') == 1 else False]
higuchi     = [True if patch.getint('metrics', 'higuchi') == 1 else False]
hurst       = [True if patch.getint('metrics', 'hurst') == 1 else False]


if debug>2:
    print('taper     = ', taper)
    print('frequency = ', frequency)

begsample = -1
endsample = -1

# create list of prefixes for Redis
computed_metrics = []
if svd[0] == True:
    computed_metrics.append('svd')
if higuchi[0] == True:
    computed_metrics.append('higuchi')
if hurst[0] == True:
    computed_metrics.append('hurst')


while True:
    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    hdr_input = ftc.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        print("Error: buffer reset detected")
        raise SystemExit
    endsample = hdr_input.nSamples - 1
    if endsample<window:
        # not enough data, try again in the next iteration
        continue

    begsample = endsample-window+1
    dat = ftc.getData([begsample, endsample]).astype(np.double)

    dat = dat[:, chanindx]
    meandat = dat.mean(0)

    # subtract the channel mean and apply the taper to each sample
    for chan in range(dat.shape[1]):
        for sample in range(dat.shape[0]):
            dat[sample, chan] -= meandat[chan]
            dat[sample, chan] *= taper[sample]

    dat_avg = np.average(dat, axis=1)

    # compute complexity over the sample direction
    cp = complexity(dat_avg, sampling_rate=hdr_input.fSample, shannon=False, sampen=False, multiscale=False, spectral=False, svd=svd[0], correlation=False, higushi=higuchi[0], petrosian=False, fisher=False, hurst=hurst[0], dfa=False, lyap_r=False, lyap_e=False)
    metric_names = list(cp.keys())

    if debug > 0:
        print(cp)
        print(metric_names)

    for i, metric in enumerate(computed_metrics):
        key = "%s" % (metric)
        comp_val = cp[metric_names[i]]
        patch.setvalue(key, comp_val)
