#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 10:15:25 2019

@author: pi
"""

#!/usr/bin/env python

# Preprocessing performs basic signal processing to data in a FieldTrip buffer,
# and puts this in a second FieldTrip buffer for further processing.
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
import redis
import argparse
import os
import sys
import time
import numpy as np
from scipy.signal import butter, lfilter_zi, lfilter

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
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# get the options from the configuration file
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('input_fieldtrip', 'timeout')

try:
    ftc_host = patch.getstring('input_fieldtrip','hostname')
    ftc_port = patch.getint('input_fieldtrip','port')
    if debug>0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug>0:
        print("Connected to input FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to input FieldTrip buffer")

try:
    ftc_host = patch.getstring('output_fieldtrip','hostname')
    ftc_port = patch.getint('output_fieldtrip','port')
    if debug>0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug>0:
        print("Connected to output FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to output FieldTrip buffer")

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
 
window = patch.getfloat('processing', 'window')
window = int(np.rint(window * hdr_input.fSample))
warmstart_dc = patch.getfloat('processing', 'warmstartoffset')
previous_dc = np.zeros(window) + warmstart_dc
previous_raw = np.zeros(window)
beg = 0
end = window
highcut = patch.getfloat("processing", "highcut")

# initialize filter
nyq = 0.5 * hdr_input.fSample
highcut = highcut / nyq
b, a = butter(3, highcut, btype='lowpass')
zi = lfilter_zi(b, a)

# jump to the end of the stream
if hdr_input.nSamples - 1 < window:
    beg = 0
    end = window - 1
else:
    beg = hdr_input.nSamples - window
    end = hdr_input.nSamples - 1

ft_output.putHeader(hdr_input.nChannels, hdr_input.fSample, FieldTrip.DATATYPE_FLOAT32, labels=hdr_input.labels)

while True:
    
    print("preprocessing")
    
    # determine when we start polling for available data
    start = time.time()
    
    while end > hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if (hdr_input.nSamples - 1) < (end-window):
            print("Error: buffer reset detected")
            raise SystemExit
        if (time.time() - start) > timeout:
            print("Error: timeout while waiting for data")
            raise SystemExit
            
    raw = np.mean(ft_input.getData([beg, end]).astype(np.float32))
    
    dcblocked = raw - previous_raw + 0.999 * previous_dc
    
    previous_dc = dcblocked
    previous_raw = raw
    
    filtered, zi = lfilter(b, a, dcblocked, zi=zi)
    
    # write the filtered, offset-corrected data to the output buffer
    output = np.reshape(filtered, (window, 1))

    ft_output.putData(output.astype(np.float32))
    
    # increment the indices for the next iteration
    beg += window
    end += window   
  