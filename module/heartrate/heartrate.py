#!/usr/bin/env python

import ConfigParser
import os
import redis
import sys
import numpy
import mne
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
import FieldTrip

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

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

H = None
while H is None:
    if debug>0:
        print "Waiting for data to arrive..."
    H = ftc.getHeader()
    time.sleep(0.2)

if debug>1:
    print H
    print H.labels

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

channel = config.getint('input','channel')-1                        # one-offset in the ini file, zero-offset in the code
window  = round(config.getfloat('processing','window') * H.fSample) # in samples

filter_length = '3s'

while True:
    time.sleep(config.getfloat('general','delay'))

    H = ftc.getHeader()
    if H.nSamples < window:
        # there are not yet enough samples in the buffer
        pass

    # we keep last up_period seconds of signal in the ECG channel
    start = H.nSamples - int(window)
    stop  = H.nSamples-1
    ECG   = ftc.getData([start,stop])[:,channel]

    Beats = mne.preprocessing.ecg.qrs_detector(H.fSample,ECG.astype(float),filter_length=filter_length)
    val = len(Beats)*H.fSample*60/window;

    key = "%s.channel%d" % (config.get('output','prefix'), channel+1)
    val = r.set(key, val)
