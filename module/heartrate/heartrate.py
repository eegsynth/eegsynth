#!/usr/bin/env python

import ConfigParser
import os
import redis
import sys
import numpy
import mne
import time

# eegsynth/lib contains shared modules
sys.path.insert(0, '../../lib')
import FieldTrip

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'heartrate.ini'))

ftc = FieldTrip.Client()

ftr_host = config.get('fieldtrip','hostname')
ftr_port = config.getint('fieldtrip','port')

print 'Trying to connect to buffer on %s:%i ...' % (ftr_host, ftr_port)
ftc.connect(ftr_host, ftr_port)
print 'Connected'

H = ftc.getHeader()
print 'Header loaded'

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

###### Parameters
# for qrs_detector function
Fs = H.fSample
filter_length = str(config.getint('QRS_detection','windows_length')/10)+'s'
# Others
waiting = config.getint('QRS_detection','waiting')
channel = config.getint('fieldtrip','channel')
window  = config.getint('QRS_detection','windows_length')*Fs

while True:
    H = ftc.getHeader()
    if H.nSamples > window:
    # There are enough samples in the buffer
        time.sleep(1)
        # we keep last up_period seconds of signal in the ECG channel
        start = H.nSamples - int(window)
        stop  = H.nSamples-1
        ECG   = ftc.getData([start,stop])[:,channel]

        Beats = mne.preprocessing.ecg.qrs_detector(Fs,ECG.astype(float),filter_length=filter_length)
        pulse = len(Beats)*Fs*60/window;
        print(pulse,H.nSamples)

        val = r.set(config.get('output', 'control'), pulse)
