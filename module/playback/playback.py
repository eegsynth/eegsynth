#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
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
import EDF

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

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
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

if debug>0:
    print "Reading data from", config.get('playback', 'file')

f = EDF.EDFReader()
f.open(config.get('playback', 'file'))

if debug>1:
    print "NSignals", f.getNSignals()
    print "SignalFreqs", f.getSignalFreqs()
    print "NSamples", f.getNSamples()
    print "SignalTextLabels", f.getSignalTextLabels()

for chanindx in range(f.getNSignals()):
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
#D = np.ndarray(shape=(H.nSamples, H.nChannels), dtype=np.float32)
#for chanindx in range(H.nChannels):#
#    D[:,chanindx] = f.readSignal(chanindx)

blocksize = int(config.getfloat('playback', 'blocksize')*H.fSample)
begsample = 0
endsample = blocksize-1
block     = 0
adjust    = 1

while True:
    if endsample>H.nSamples-1:
        if debug>0:
            print "End of file reached, jumping back to start"
        begsample = 0
        endsample = blocksize-1
        block     = 0
        continue

    if EEGsynth.getint('playback', 'rewind', config, r):
        if debug>0:
            print "Rewind pressed, jumping back to start of file"
        begsample = 0
        endsample = blocksize-1
        block     = 0
        continue

    if not EEGsynth.getint('playback', 'play', config, r):
        if debug>0:
            print "Paused"
        time.sleep(0.1);
        continue

    # measure the time that it takes
    now = time.time()

    if debug>1:
        print "Playing section", block, 'from', begsample, 'to', endsample

    D = np.ndarray(shape=(blocksize, H.nChannels), dtype=np.float32)
    for chanindx in range(H.nChannels):
        D[:,chanindx] = f.readSamples(chanindx, begsample, endsample)

    ftc.putData(D)

    # this approximates the real time streaming speed
    desired = blocksize/(H.fSample*EEGsynth.getfloat('playback', 'speed', config, r))
    # the adjust factor compensates for the time spent on reading and writing the data
    time.sleep(adjust * desired);

    begsample += blocksize
    endsample += blocksize
    block += 1

    elapsed = time.time() - now
    # adjust the relative delay for the next iteration
    # the adjustment factor should only change a little per iteration
    adjust = 0.1 * desired/elapsed + 0.9 * adjust
