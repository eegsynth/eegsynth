#!/usr/bin/env python

# Playback plays back raw data from file to the FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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
import numpy as np
import os
import redis
import sys
import time
import wave
import struct

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
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth
import FieldTrip
import EDF

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--inifile', default=os.path.join(path, name + '.ini'), help='name of the configuration file')
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError('cannot connect to Redis server')

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug       = patch.getint('general','debug')
filename    = patch.getstring('playback', 'file')
fileformat  = patch.getstring('playback', 'format')

if fileformat is None:
    # determine the file format from the file name
    name, ext = os.path.splitext(filename)
    fileformat = ext[1:]

monitor.info('Reading data from ' + filename)

try:
    ft_host = patch.getstring('fieldtrip','hostname')
    ft_port = patch.getint('fieldtrip','port')
    monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
    ft_output = FieldTrip.Client()
    ft_output.connect(ft_host, ft_port)
    monitor.success('Connected to FieldTrip buffer')
except:
    raise RuntimeError('cannot connect to FieldTrip buffer')

H = FieldTrip.Header()

MININT8  = -np.power(2.,7)
MAXINT8  =  np.power(2.,7)-1
MININT16 = -np.power(2.,15)
MAXINT16 =  np.power(2.,15)-1
MININT32 = -np.power(2.,31)
MAXINT32 =  np.power(2.,31)-1

if fileformat=='edf':
    f = EDF.EDFReader()
    f.open(filename)
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
        monitor.info('reading channel ' + str(chanindx))
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
    f = wave.open(filename, 'r')
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
        x = struct.unpack_from ('%dh' % f.getnframes()*f.getnchannels(), x)
        x = np.asarray(x).astype(np.float32).reshape(f.getnframes(), f.getnchannels())
        y = x / float(MAXINT16)
    elif resolution==4:
        x = struct.unpack_from ('%di' % f.getnframes()*f.getnchannels(), x)
        x = np.asarray(x).astype(np.float32).reshape(f.getnframes(), f.getnchannels())
        y = x / float(MAXINT32)
    else:
        raise NotImplementedError('unsupported resolution')
    A = y * ((physical_max-physical_min)/2)

else:
    raise NotImplementedError('unsupported file format')

monitor.debug('nChannels = ' + str(H.nChannels))
monitor.debug('nSamples = ' + str(H.nSamples))
monitor.debug('fSample = '+ str(H.fSample))
monitor.debug('labels = ' + str(labels))

ft_output.putHeader(H.nChannels, H.fSample, H.dataType, labels=labels)

blocksize = int(patch.getfloat('playback', 'blocksize')*H.fSample)
begsample = 0
endsample = blocksize-1
block     = 0

while True:
    monitor.loop()

    if endsample>H.nSamples-1:
        monitor.info('End of file reached, jumping back to start')
        begsample = 0
        endsample = blocksize-1
        block     = 0

    if patch.getint('playback', 'rewind', default=0):
        monitor.info('Rewind pressed, jumping back to start of file')
        begsample = 0
        endsample = blocksize-1
        block     = 0

    if not patch.getint('playback', 'play', default=1):
        monitor.info('Stopped')
        time.sleep(0.1);
        continue

    if patch.getint('playback', 'pause', default=0):
        monitor.info('Paused')
        time.sleep(0.1);
        continue

    # measure the time to correct for the slip
    start = time.time()

    monitor.info('Playing block ' + str(block) + ' from ' + str(begsample) + ' to ' + str(endsample))

    # copy the selected samples from the in-memory data
    D = A[begsample:endsample+1,:]

    # write the data to the output buffer
    ft_output.putData(D)

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

    monitor.info('played ' + str(blocksize) + ' samples in ' str((time.time()-start)*1000) + ' ms')
