#!/usr/bin/env python

import pyaudio
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import wave
import time
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
import EEGsynth
import FieldTrip

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

p = pyaudio.PyAudio()

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

hdr = None
while hdr is None:
    if debug>0:
        print "Waiting for data to arrive..."
    hdr = ftc.getHeader()
    time.sleep(0.2)

if debug>1:
    print hdr
    print hdr.labels

buf = np.zeros([44100, 1]);
buf = np.empty([0, 1]);

def callback(in_data, frame_count, time_info, status):
    print config
    print buf
    print "yes"
    if buf.shape[0]<frame_count:
        dat = np.zeros(frame_count)
    else:
        dat = buf[1:frame_count]         # copy the first data from the buf
        buf = buf[-frame_count:]      # remove it from the buf
    return (dat, pyaudio.paContinue)

format = config.getint('audio','format')
rate = config.getint('audio','rate')
window = config.getint('fieldtrip','window')*hdr.fSample

stream = p.open(format=format,
                channels=1,
                rate=rate,
                output=True,
                stream_callback=callback)

stream.start_stream()

begsample = -1
while begsample<0:
    # wait until there is enough data
    hdr = ftc.getHeader()
    # jump to the end of the stream
    begsample = int(hdr.nSamples - window)
    endsample = int(hdr.nSamples - 1)

    while endsample>hdr.nSamples-1:
        # wait until there is enough data
        time.sleep(config.getfloat('general', 'delay'))
        hdr = ftc.getHeader()

    dat = ftc.getData([begsample, endsample])

    if buf is None:
        buf = dat;
    else:
        print buf.shape
        print dat.shape
        buf = np.concatenate([buf, dat])

stream.stop_stream()
stream.close()

p.terminate()
