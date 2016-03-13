#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import edflib

import numpy as np

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'playback.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    ftr_host = config.get('fieldtrip','hostname')
    ftr_port = config.getint('fieldtrip','port')
    print 'Trying to connect to buffer on %s:%i ...' % (ftr_host, ftr_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftr_host, ftr_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()


f = edflib.EdfReader(config.get('playback', 'file'))

print f.getSignalTextLabels()
print f.getNSamples()
print f.getSignalFreqs()

nchans    = len(f.getSignalFreqs())
fsample   = f.getSignalFreqs()[0]
nsamples  = f.getNSamples()[0]
blocksize = int(round(config.getfloat('playback', 'blocksize')*fsample))

H = FieldTrip.Header()

H.nChannels = nchans
H.nSamples  = 0
H.nEvents   = 0
H.fSample   = fsample
H.dataType  = FieldTrip.DATATYPE_FLOAT32

D   = np.ndarray(shape=(nchans, blocksize), dtype=np.float64)

# print H
# print D

begsample = 1.0
endsample = blocksize

block = 0

while True:

    block += 1

    if endsample>nsamples:
        exit()

    print block, begsample/fsample, endsample/fsample

    buf = np.zeros(blocksize*nchans, dtype=np.float64)
    for chanindx in range(nchans):
        v = buf[chanindx*blocksize:(chanindx+1)*blocksize]
        f.readsignal(chanindx, begsample/fsample, endsample/fsample, v)

    for chanindx in range(nchans):
        D[chanindx,:] = buf[chanindx*blocksize:(chanindx+1)*blocksize]

    exit()

    begsample += blocksize
    endsample += blocksize

    H.nSamples  += blocksize
