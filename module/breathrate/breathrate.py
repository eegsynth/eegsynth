#!/usr/bin/env python

# breathrate identifies inhalation peaks in breathing belt signals and uses
# them to calculate breathing rate based on peak-to-peak interval
#
# This software is part of the EEGsynth project,
# see https://github.com/eegsynth/eegsynth
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
import os
import redis
import sys
import time
import numpy as np

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
sys.path.insert(0, os.path.join(path,'../../lib'))
import FieldTrip
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument('-i',
                    '--inifile',
                    default=os.path.join(path,
                                         os.path.splitext(file)[0] + '.ini'),
                    help='optional name of the configuration file')
args = parser.parse_args()
config = configparser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'),
                          port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError('cannot connect to Redis server')
    
# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# get the options from the configuration file
debug = patch.getint('general', 'debug')
timeout = patch.getfloat('fieldtrip', 'timeout')
channel = patch.getint('input', 'channel') - 1                                 
key_rate = patch.getstring('output', 'key')
window = patch.getfloat('processing', 'window')
stride = patch.getfloat('general', 'delay')
lrate = patch.getfloat('processing', 'lrate')

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on {}:{} ...'.format(ftc_host,
              ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print('connected to input FieldTrip buffer')
except:
    raise RuntimeError('cannot connect to input FieldTrip buffer')
    
hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print('waiting for data to arrive...')
    if (time.time() - start) > timeout:
        print('error: timeout while waiting for data')
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.1)

if debug>0:
    print('data arrived')
if debug>1:
    print(hdr_input)
    print(hdr_input.labels)
    
sfreq = hdr_input.fSample
window = int(np.rint(window * sfreq))

# initiate variables
state = 'wrc'
maxbr = 100
micsfact = 0.5
mdcsfact = 0.1
ics = np.nan
dcs = np.nan
mics = np.int(np.rint((micsfact * 60/maxbr) * sfreq))
mdcs = np.int(np.rint((mdcsfact * 60/maxbr) * sfreq))
lowtafact = 0.25
meanta = 0
stdta = 0
lastrisex = 0
lastfallx = 0
lastpeak = np.nan
currentmin = np.inf
currentmax = -np.inf
begsample = -1
endsample = -1
n = 0

while True:
    # window shift implicitely controlled with temporal delay; to
    # be able to change this "on the fly" read out stride from the patch
    # inside the loop if desired
    time.sleep(stride)
    
    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        print('error: buffer reset detected')
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug > 0:
            print('waiting for data...')
        continue
    
    # grab the next window
    begsample = hdr_input.nSamples - int(window)
    endsample = hdr_input.nSamples - 1
    block_idcs = np.arange(begsample, endsample, dtype=int)
    dat = ft_input.getData([begsample, endsample])
    dat = dat[:, channel]
    
    # find zero-crossings
    greater = dat > 0
    smaller = dat <= 0
    
    if state == 'wrc':
    
        # search for rising crossing
        risex = np.where(np.bitwise_and(greater[1:], smaller[:-1]))[0]
        
        if risex.size == 0:
            # update current minimum
            if np.min(dat) < currentmin:
                currentmin = np.min(dat)
                # -1 is neccessary in case argmin is last index (otherwise
                # index is out of bound)
                currentmin_idx = block_idcs[np.argmin(dat) - 1] 
            continue
        
        risex = risex[-1]
        risex_idx = block_idcs[risex]
        ics = risex_idx - lastrisex
        dcs = risex_idx - lastfallx
        if np.logical_and(ics > mics, dcs > mdcs):

            lastrisex = risex_idx
            # update current minimum
            if np.min(dat[:risex]) < currentmin:
                currentmin = np.min(dat[:risex])
                currentmin_idx = block_idcs[np.argmin(dat[:risex])]
            # update current maximum
            currentmax = np.max(dat[risex:])
            currentmax_idx = block_idcs[np.argmax(dat[risex:])]
            # switch state
            state = 'wfc'
        
        
    elif state == 'wfc':
    
        # search for falling crossing
        fallx = np.where(np.bitwise_and(smaller[1:], greater[:-1]))[0]
            
        if fallx.size == 0:
            # update current maximum
            if np.max(dat) > currentmax:
                currentmax = np.max(dat)
                currentmax_idx = block_idcs[np.argmax(dat) - 1]
            continue
            
        fallx = fallx[-1]
        fallx_idx = block_idcs[fallx]
        ics = fallx_idx - lastfallx
        dcs = fallx_idx - lastrisex
        if np.logical_and(ics > mics, dcs > mdcs): 
        
            lastfallx = fallx_idx
            # update current maximum
            if np.max(dat[:fallx]) > currentmax:
                currentmax = np.max(dat[:fallx])
                currentmax_idx = block_idcs[np.argmax(dat[:fallx])]
            # apply a threshold to the tidal amplitude; tidal amplitude
            # is defined as vertical distance of through to peak
            currentta = currentmax - currentmin
            # assume normal distribution over tidal amplitude values as well as
            # stationarity of the signal, estimate the 80th percentile based
            # on mean and standard deviation
            
            # get real-time estimates of mean and std
            n += 1
            lastmeanta = meanta
            meanta = (meanta + (currentta - meanta) / (n))
            stdta = np.sqrt(stdta + (currentta - meanta) * (currentta - lastmeanta))
            # define typical tidal amplitude as 84th percentile
            typta = meanta + stdta
            # and apply the threshold weight to the typical amplitude
            lowta = typta * lowtafact
            print(lowta, currentta)

            if currentta > lowta:
                #declare the current maximum a valid peak
                peak = currentmax_idx
                if np.isnan(lastpeak):
                    lastpeak = peak
                    continue
                rate = (60 / ((peak - lastpeak) / sfreq))
                print('BREATH DETECTED')
                # publish rate
                patch.setvalue(key_rate, rate, debug=debug)
                lastpeak = peak
            # update current minimum
            currentmin = np.min(dat[fallx:])
            currentmin_idx = block_idcs[np.argmin(dat[fallx:])]
            # switch state
            state = 'wrc'
                   