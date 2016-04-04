#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import edflib
import numpy as np
import datetime

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
config.read(os.path.join(installed_folder, 'recording.ini'))

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

H = None
while H is None:
    ftr_host = config.get('fieldtrip','hostname')
    ftr_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftr_host, ftr_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftr_host, ftr_port)
    H = ftc.getHeader()

if debug>0:
    print "Connected to FieldTrip buffer"

if debug>1:
    print H
    print H.labels

blocksize  = int(config.getfloat('recording', 'blocksize')*H.fSample)
fileopen   = False
filenumber = 0

while True:
    if not EEGsynth.getint('recording', 'record', config, r):
        if fileopen:
            # close the exising file
            if debug>0:
                print "Closing", fname
            f.close()
            fileopen = False
        if debug>0:
            print "Not recording"
        time.sleep(0.1);
        continue

    if not fileopen:
        # open a new file, they get a sequence number
        fname = config.get('recording', 'file')
        name, ext = os.path.splitext(fname)
        fname = name + '-' + str(filenumber) + ext
        if debug>0:
            print "Opening", fname
        f = EDF.EDFWriter(fname)
        fileopen = True
        # construct the header
        meas_info = {}
        chan_info = {}
        meas_info['record_length']  = blocksize/H.fSample
        meas_info['nchan']          = H.nChannels
        now = datetime.datetime.now()
        meas_info['year']           = now.year
        meas_info['month']          = now.month
        meas_info['day']            = now.day
        meas_info['hour']           = now.hour
        meas_info['minute']         = now.minute
        meas_info['second']         = now.second
        chan_info['physical_min']   = H.nChannels * [-100.] # FIXME
        chan_info['physical_max']   = H.nChannels * [ 100.]
        chan_info['digital_min']    = H.nChannels * [-32768]
        chan_info['digital_max']    = H.nChannels * [ 32768]
        chan_info['ch_names']       = H.labels
        chan_info['n_samps']        = H.nChannels * [blocksize]
        print chan_info
        # write the header to file
        f.writeHeader((meas_info, chan_info))
        # determine the starting point for recording
        H = ftc.getHeader()
        endsample = H.nSamples - 1
        begsample = endsample - blocksize + 1


    H = ftc.getHeader()
    if endsample>H.nSamples-1:
        continue

    D = ftc.getData([begsample, endsample])
    if debug>0:
        print "Writing sample", begsample, "to", endsample

    f.writeBlock(D)

    begsample += blocksize
    endsample += blocksize
