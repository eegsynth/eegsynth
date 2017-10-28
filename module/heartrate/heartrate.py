#!/usr/bin/env python

import ConfigParser
import os
import redis
import sys
import numpy as np
import mne
import time
import argparse

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

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

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

filter_length = '3s'
window  = round(config.getfloat('processing','window') * H.fSample) # in samples
channel = config.getint('input','channel')-1                        # one-offset in the ini file, zero-offset in the code
key     = "%s.channel%d" % (config.get('output','prefix'), channel+1)

while True:
    time.sleep(config.getfloat('general','delay'))

    H = ftc.getHeader()
    if H.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug>0:
            print "waiting for data"
        continue

    # we process the last window from the ECG channel
    start = H.nSamples - int(window)
    stop  = H.nSamples-1
    ECG   = ftc.getData([start,stop])[:,channel]

    beats = mne.preprocessing.ecg.qrs_detector(H.fSample,ECG.astype(float),filter_length=filter_length)
    val = float(60./(np.mean(np.diff(beats))/H.fSample))

    if debug>1:
        print key, val
    if not np.isnan(val):
        r.set(key, val)
