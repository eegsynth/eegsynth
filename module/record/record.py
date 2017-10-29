#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import datetime
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
import FieldTrip
import EDF

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

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

H = None
while H is None:
    if debug>0:
        print "Waiting for data to arrive..."
    H = ftc.getHeader()
    time.sleep(0.2)

if debug>1:
    print H
    print H.labels

filenumber = 0
recording = False

while True:
    H = ftc.getHeader()

    if recording and H is None:
        if debug>0:
            print "Header is empty - closing", fname
        f.close()
        recording = False
        continue

    if recording and not EEGsynth.getint('recording', 'record', config, r):
        if debug>0:
            print "Recording disabled - closing", fname
        f.close()
        recording = False
        continue

    if not recording and not EEGsynth.getint('recording', 'record', config, r):
        if debug>0:
            print "Recording is not enabled"
        time.sleep(1)

    if not recording and EEGsynth.getint('recording', 'record', config, r):
        recording = True
        # open a new file
        fname = config.get('recording', 'file')
        name, ext = os.path.splitext(fname)
        fname = name + '-' + str(filenumber) + ext
        while os.path.isfile(fname):
            # increase the sequence number
            filenumber += 1
            fname = name + '-' + str(filenumber) + ext
        # the blocksize depends on the sampling rate, which may have changed
        blocksize = int(config.getfloat('recording', 'blocksize')*H.fSample)
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
        chan_info['physical_min']   = H.nChannels * [-10000.] # FIXME
        chan_info['physical_max']   = H.nChannels * [ 10000.]
        chan_info['digital_min']    = H.nChannels * [-32768]
        chan_info['digital_max']    = H.nChannels * [ 32768]
        chan_info['ch_names']       = H.labels
        chan_info['n_samps']        = H.nChannels * [blocksize]
        # write the header to file
        if debug>0:
            print "Opening", fname
        f = EDF.EDFWriter(fname)
        f.writeHeader((meas_info, chan_info))
        # determine the starting point for recording
        if H.nSamples>blocksize:
            endsample = H.nSamples - 1
            begsample = endsample - blocksize + 1
        else:
            endsample = blocksize - 1
            begsample = endsample - blocksize + 1

    if recording and H.nSamples<begsample-1:
        if debug>0:
            print "Header was reset - closing", fname
        f.close()
        recording = False
        continue

    if recording and endsample>H.nSamples-1:
        if debug>2:
            print "Waiting for data", endsample, H.nSamples
        time.sleep((endsample-H.nSamples)/H.fSample)
        continue

    if recording:
        D = ftc.getData([begsample, endsample])
        if debug>0:
            print "Writing sample", begsample, "to", endsample, "as", np.shape(D)
        f.writeBlock(np.transpose(D))
        begsample += blocksize
        endsample += blocksize
