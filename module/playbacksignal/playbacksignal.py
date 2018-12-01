#!/usr/bin/env python

# Playback plays back raw data from file to the FieldTrip buffer
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time
import wave
import struct

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

try:
    ftc_host = patch.getstring('fieldtrip','hostname')
    ftc_port = patch.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

try:
    fileformat = patch.getstring('playback', 'format')
except:
    fname = patch.getstring('playback', 'file')
    name, ext = os.path.splitext(fname)
    fileformat = ext[1:]

if debug>0:
    print "Reading data from", patch.getstring('playback', 'file')

H = FieldTrip.Header()

MININT8  = -np.power(2,7)
MAXINT8  =  np.power(2,7)-1
MININT16 = -np.power(2,15)
MAXINT16 =  np.power(2,15)-1
MININT32 = -np.power(2,31)
MAXINT32 =  np.power(2,31)-1

if fileformat=='edf':
    f = EDF.EDFReader()
    f.open(patch.getstring('playback', 'file'))
    for chanindx in range(f.getNSignals()):
        if f.getSignalFreqs()[chanindx]!=f.getSignalFreqs()[0]:
            raise AssertionError('unequal SignalFreqs')
        if f.getNSamples()[chanindx]!=f.getNSamples()[0]:
            raise AssertionError('unequal NSamples')
    H.nChannels = len(f.getSignalFreqs())
    H.fSample   = f.getSignalFreqs()[0]
    H.nSamples  = f.getNSamples()[0]
    H.nEvents   = 0
    H.dataType  = FieldTrip.DATATYPE_FLOAT32
    # the channel labels will be written to the buffer
    labels = f.getSignalTextLabels()
    # read all the data from the file
    A = np.ndarray(shape=(H.nSamples, H.nChannels), dtype=np.float32)
    for chanindx in range(H.nChannels):
        print "reading channel", chanindx
        A[:,chanindx] = f.readSignal(chanindx)
    f.close()

elif fileformat=='wav':
    try:
        physical_min = patch.getfloat('playback', 'physical_min')
    except:
        physical_min = -1
    try:
        physical_max = patch.getfloat('playback', 'physical_max')
    except:
        physical_max =  1
    f = wave.open(patch.getstring('playback', 'file'), 'r')
    resolution = f.getsampwidth() # 1, 2 or 4
    # 8-bit samples are stored as unsigned bytes, ranging from 0 to 255.
    # 16-bit samples are stored as signed integers in 2's-complement.
    H.nChannels = f.getnchannels()
    H.fSample   = f.getframerate()
    H.nSamples  = f.getnframes()
    H.nEvents   = 0
    H.dataType  = FieldTrip.DATATYPE_FLOAT32
    # there are no channel labels
    labels = None
    # read all the data from the file
    x = f.readframes(f.getnframes()*f.getnchannels())
    f.close()
    # convert and calibrate
    if resolution==2:
        x = struct.unpack_from ("%dh" % f.getnframes()*f.getnchannels(), x)
        x = np.asarray(x).astype(np.float32).reshape(f.getnframes(), f.getnchannels())
        y = x / float(MAXINT16)
    elif resolution==4:
        x = struct.unpack_from ("%di" % f.getnframes()*f.getnchannels(), x)
        x = np.asarray(x).astype(np.float32).reshape(f.getnframes(), f.getnchannels())
        y = x / float(MAXINT32)
    else:
        raise NotImplementedError('unsupported resolution')
    A = y * ((physical_max-physical_min)/2)

else:
    raise NotImplementedError('unsupported file format')

if debug>1:
    print "nChannels", H.nChannels
    print "nSamples", H.nSamples
    print "fSample", H.fSample
    print "labels", labels

ftc.putHeader(H.nChannels, H.fSample, H.dataType, labels=labels)

blocksize = int(patch.getfloat('playback', 'blocksize')*H.fSample)
begsample = 0
endsample = blocksize-1
block     = 0

print "STARTING STREAM"
while True:

    if endsample>H.nSamples-1:
        if debug>0:
            print "End of file reached, jumping back to start"
        begsample = 0
        endsample = blocksize-1
        block     = 0

    if patch.getint('playback', 'rewind', default=0):
        if debug>0:
            print "Rewind pressed, jumping back to start of file"
        begsample = 0
        endsample = blocksize-1
        block     = 0

    if not patch.getint('playback', 'play', default=1):
        if debug>0:
            print "Stopped"
        time.sleep(0.1);
        continue

    if patch.getint('playback', 'pause', default=0):
        if debug>0:
            print "Paused"
        time.sleep(0.1);
        continue

    # measure the time that it takes
    start = time.time()

    if debug>0:
        print "Playing block", block, 'from', begsample, 'to', endsample

    # copy the selected samples from the in-memory data
    D = A[begsample:endsample+1,:]

    # write the data to the output buffer
    ftc.putData(D)

    begsample += blocksize
    endsample += blocksize
    block += 1

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = blocksize/(H.fSample*patch.getfloat('playback', 'speed'))
    elapsed = time.time()-start
    naptime = desired - elapsed
    if naptime>0:
        # this approximates the real time streaming speed
        time.sleep(naptime)

    if debug>0:
        print "played", blocksize, "samples in", (time.time()-start)*1000, "ms"
