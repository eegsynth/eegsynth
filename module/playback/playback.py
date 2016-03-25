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
import EEGsynth

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'playback.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

try:
    ftr_host = config.get('fieldtrip','hostname')
    ftr_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftr_host, ftr_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftr_host, ftr_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

if debug>0:
    print "Reading data from", config.get('playback', 'file')

f = edflib.EdfReader(config.get('playback', 'file'))

if debug>1:
    print 'SignalTextLabels = ', f.getSignalTextLabels()
    print 'NSamples         = ', f.getNSamples()
    print 'SignalFreqs      = ', f.getSignalFreqs()

for chanindx in range(f.signals_in_file):
    if f.getSignalFreqs()[chanindx]!=f.getSignalFreqs()[0]:
        raise IOError('unequal SignalFreqs')
    if f.getNSamples()[chanindx]!=f.getNSamples()[0]:
        raise IOError('unequal NSamples')

H = FieldTrip.Header()

H.nChannels = len(f.getSignalFreqs())
H.nSamples  = f.getNSamples()[0]
H.nEvents   = 0
H.fSample   = f.getSignalFreqs()[0]
H.dataType  = FieldTrip.DATATYPE_FLOAT32

ftc.putHeader(H.nChannels, H.fSample, H.dataType, labels=f.getSignalTextLabels())

# read all the data from the file
D = np.ndarray(shape=(H.nSamples, H.nChannels), dtype=np.float32)
for chanindx in range(H.nChannels):
    D[:,chanindx] = f.readSignal(chanindx)

blocksize = int(config.getfloat('playback', 'blocksize')*H.fSample)
begsample = 0
endsample = blocksize-1
block     = 1

while True:
    if endsample>H.nSamples:
        if debug>0:
            print "End of file reached, jumping back to start"
        begsample = 0
        endsample = blocksize-1
        continue

    if EEGsynth.getint('playback', 'rewind', config, r):
        if debug>0:
            print "Rewind pressed, jumping back to start of file"
        begsample = 0
        endsample = blocksize-1

    if not EEGsynth.getint('playback', 'play', config, r):
        if debug>0:
            print "Paused"
        time.sleep(0.1);
        continue

    if debug>1:
        print "Playing section", block, 'from', begsample, 'to', endsample

    ftc.putData(D[begsample:(endsample+1),:])

    # this approximates the real time streaming speed
    time.sleep(blocksize/(EEGsynth.getfloat('playback', 'speed', config, r)*H.fSample));

    begsample += blocksize
    endsample += blocksize
    block += 1
