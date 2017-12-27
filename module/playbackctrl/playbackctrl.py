#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
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
import EDF

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

if debug>0:
    print "Reading data from", patch.getstring('playback', 'file')

f = EDF.EDFReader()
f.open(patch.getstring('playback', 'file'))

if debug>1:
    print "NSignals", f.getNSignals()
    print "SignalFreqs", f.getSignalFreqs()
    print "NSamples", f.getNSamples()
    print "SignalTextLabels", f.getSignalTextLabels()

for chanindx in range(f.getNSignals()):
    if f.getSignalFreqs()[chanindx]!=f.getSignalFreqs()[0]:
        raise AssertionError('unequal SignalFreqs')
    if f.getNSamples()[chanindx]!=f.getNSamples()[0]:
        raise AssertionError('unequal NSamples')

channels = f.getSignalTextLabels()
channelz = f.getSignalTextLabels()

fSample = f.getSignalFreqs()[0]
nSamples = f.getNSamples()[0]

# search-and-replace to reduce the length of the channel labels
for replace in config.items('replace'):
    print replace
    for i in range(len(channelz)):
        channelz[i] = channelz[i].replace(replace[0], replace[1])
for s,z in zip(channels, channelz):
    print "Writing channel", s, "as control value", z

blocksize = 1
begsample = 0
endsample = blocksize-1
block     = 0

print "STARTING STREAM"
while True:

    if endsample>nSamples-1:
        if debug>0:
            print "End of file reached, jumping back to start"
        begsample = 0
        endsample = blocksize-1
        block     = 0
        continue

    if patch.getint('playback', 'rewind'):
        if debug>0:
            print "Rewind pressed, jumping back to start of file"
        begsample = 0
        endsample = blocksize-1
        block     = 0
        continue

    if not patch.getint('playback', 'play'):
        if debug>0:
            print "Paused"
        time.sleep(0.1);
        continue

    # measure the time that it takes
    start = time.time()

    if debug>1:
        print "Playing control value", block, 'from', begsample, 'to', endsample

    dat = map(int, f.readBlock(block))
    r.mset(dict(zip(channelz,dat)))

    begsample += blocksize
    endsample += blocksize
    block += 1

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = blocksize/(fSample*patch.getfloat('playback', 'speed'))
    elapsed = time.time()-start
    naptime = desired - elapsed
    if naptime>0:
        # this approximates the real time streaming speed
        time.sleep(naptime)

    if debug>0:
        print "played", blocksize, "samples in", (time.time()-start)*1000, "ms"
