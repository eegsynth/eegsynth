#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np
from numpy.matlib import repmat

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

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
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug>1:
    print hdr_input
    print hdr_input.labels

smoothing = config.getfloat('processing', 'smoothing')
window = config.getfloat('processing', 'window')
window = int(round(window*hdr_input.fSample))

reference = config.get('processing','reference')

begsample = -1
while begsample<0:
    # wait until there is enough data
    hdr_input = ft_input.getHeader()
    # jump to the end of the stream
    begsample = int(hdr_input.nSamples - window)
    endsample = int(hdr_input.nSamples - 1)

ft_output.putHeader(hdr_input.nChannels, hdr_input.fSample, hdr_input.dataType, labels=hdr_input.labels)

previous = np.zeros((1, hdr_input.nChannels))

while True:
    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(config.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()

    if debug>1:
        print endsample

    dat_input = ft_input.getData([begsample, endsample])
    dat_output = dat_input.astype(np.float32)

    for t in range(window):
        dat_output[t,:] = smoothing * dat_output[t,:] + (1.-smoothing)*previous
        previous = dat_output[t,:]

    if reference == 'median':
        dat_output -= np.matlib.repmat(np.median(dat_output, axis=1), dat_output.shape[1], 1).T
    elif reference == 'mean':
        dat_output -= np.matlib.repmat(np.mean(dat_output, axis=1), dat_output.shape[1], 1).T

    # write the data to the output buffer
    ft_output.putData(dat_output)
    # increment the counters for the next loop
    begsample += window
    endsample += window
