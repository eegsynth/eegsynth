#!/usr/bin/env python

# Preprocessing performs basic signal processing to data in a FieldTrip buffer,
# and puts this in a second FieldTrip buffer for further processing.
#
# Preprocessing is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

from copy import copy
from numpy.matlib import repmat
from scipy.ndimage import convolve1d
from scipy.signal import firwin
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
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
timeout = config.getfloat('input_fieldtrip','timeout')

try:
    ftc_host = config.get('input_fieldtrip','hostname')
    ftc_port = config.getint('input_fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

try:
    ftc_host = config.get('output_fieldtrip','hostname')
    ftc_port = config.getint('output_fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
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

if debug>1:
    print hdr_input
    print hdr_input.labels

window = config.getfloat('processing', 'window')
window = int(round(window*hdr_input.fSample))

ft_output.putHeader(hdr_input.nChannels, hdr_input.fSample, hdr_input.dataType, labels=hdr_input.labels)

try:
    smoothing = config.getfloat('processing', 'smoothing')
except:
    smoothing = None

reference = config.get('processing','reference')

# Filtering init
try:
    lowpassfilter = config.getfloat('processing', 'lowpassfilter')/hdr_input.fSample
except:
    lowpassfilter = None

try:
    highpassfilter = config.getfloat('processing', 'highpassfilter')/hdr_input.fSample
except:
    highpassfilter = None

try:
    filterorder = config.getint('processing', 'filterorder')
except:
    filterorder = None

# Low pass
if not(lowpassfilter is None) and (highpassfilter is None):
    fir_poly = firwin(filterorder, cutoff = lowpassfilter, window = "hamming")
# High pass
if not(highpassfilter is None) and (lowpassfilter is None):
    fir_poly = firwin(filterorder, cutoff = highpassfilter, window = "hanning", pass_zero=False)
# Band pass
if not(highpassfilter is None) and not(lowpassfilter is None):
    fir_poly = firwin(filterorder, cutoff = [highpassfilter, lowpassfilter], window = 'blackmanharris', pass_zero = False)

def onlinefilter(fil_state, in_data):
    m = in_data.shape[0]
    n = len(fir_poly)
    fil_state = np.concatenate((fil_state, np.atleast_2d(in_data)), axis=0)
    fil_data = convolve1d(fil_state, fir_poly)
    return fil_state[-n:, :], fil_data[-m:, :]

# initialize the state for the smoothing
previous = np.zeros((1, hdr_input.nChannels))

# initialize the state for the filtering
if not(highpassfilter is None) or not(lowpassfilter is None):
    fil_state = np.zeros((filterorder, hdr_input.nChannels))

# jump to the end of the stream
if hdr_input.nSamples-1<window:
    begsample = 0
    endsample = window-1
else:
    begsample = hdr_input.nSamples-window
    endsample = hdr_input.nSamples-1

print "STARTING PREPROCESSING STREAM"
while True:
    start = time.time()

    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(config.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if (hdr_input.nSamples-1)<(endsample-window):
            print "Error: buffer reset detected"
            raise SystemExit
        if (time.time()-start)>timeout:
            print "Error: timeout while waiting for data"
            raise SystemExit

    # determine the start of the actual processing
    start = time.time()

    dat_input  = ft_input.getData([begsample, endsample])
    dat_output = dat_input.astype(np.float32)

    if debug>1:
        print "------------------------------------------------------------"
        print "read        ", window, "samples in", (time.time()-start)*1000, "ms"

    # Smoothing
    if not(smoothing is None):
        for t in range(window):
            dat_output[t, :] = smoothing * dat_output[t, :] + (1.-smoothing)*previous
            previous = copy(dat_output[t, :])
    if debug>1:
        print "smoothed    ", window, "samples in", (time.time()-start)*1000, "ms"

    # Online filtering
    if not(highpassfilter is None) or not(lowpassfilter is None):
        fil_state, dat_output = onlinefilter(fil_state, dat_output)
    if debug>1:
        print "filtered    ", window, "samples in", (time.time()-start)*1000, "ms"

    # Rereferencing
    if reference == 'median':
        dat_output -= repmat(np.nanmedian(dat_output, axis=1),
                             dat_output.shape[1], 1).T
    elif reference == 'average':
        dat_output -= repmat(np.nanmean(dat_output, axis=1),
                             dat_output.shape[1], 1).T
    if debug>1:
        print "rereferenced", window, "samples in", (time.time()-start)*1000, "ms"

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32))

    if debug==1:
        print "preprocessed", window, "samples in", (time.time()-start)*1000, "ms"
    if debug>1:
        print "wrote       ", window, "samples in", (time.time()-start)*1000, "ms"

    # increment the counters for the next loop
    begsample += window
    endsample += window
