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
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug = patch.getint('general','debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

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

prefix      = patch.getstring('output', 'prefix')

begsample = -1
endsample = -1

while True:

    window = patch.getfloat('processing', 'window') * \
             patch.getfloat('scale', 'window') + \
             patch.getfloat('offset', 'window')  # in seconds

    if debug > 1:
        print('window = ', window, 'seconds')

    window = int(round(window * hdr_input.fSample))  # in samples
    taper = np.hanning(window)
    frequency = np.fft.rfftfreq(window, 1.0 / hdr_input.fSample)

    if debug > 1:
        print('window = ', window, 'samples')

    if debug > 2:
        print('taper     = ', taper)
        print('frequency = ', frequency)

    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    band_items = config.items('band')
    bandname = []
    bandlo   = []
    bandhi   = []
    for item in band_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        lohi = patch.getfloat('band', item[0], multiple=True)
        if debug>2:
            print(item[0], lohi)
        bandname.append(item[0])
        bandlo.append(lohi[0])
        bandhi.append(lohi[1])
    if debug>0:
        print(bandname, bandlo, bandhi)

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

    # FIXME it should be possible to do this differently
    power = []
    for chan in channame:
        for band in bandname:
            power.append(0)

    dat = dat[:, chanindx]
    meandat = dat.mean(0)

    # FIXME use detrend just like plotspectral
    # FIXME multiply with taper in one go

    # subtract the channel mean and apply the taper to each sample
    for chan in range(dat.shape[1]):
        for sample in range(dat.shape[0]):
            dat[sample, chan] -= meandat[chan]
            dat[sample, chan] *= taper[sample]

    # compute the FFT over the sample direction
    F = np.fft.rfft(dat, axis=0)

    i = 0
    for chan in range(F.shape[1]):
        for lo,hi in zip(bandlo,bandhi):
            power[i] = 0
            count = 0
            for sample in range(len(frequency)):
                if frequency[sample]>=lo and frequency[sample]<=hi:
                    power[i] += abs(F[sample, chan]*F[sample, chan])
                    count    += 1
            if count>0:
                power[i] /= count
            i+=1

    if debug>1:
        print(power)

    i = 0
    for chan in channame:
        for band in bandname:
            key = "%s.%s.%s" % (prefix, chan, band)
            patch.setvalue(key, power[i])
            i+=1
