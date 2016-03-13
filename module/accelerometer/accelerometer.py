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
import EEGsynth

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'accelerometer.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    ftr_host = config.get('fieldtrip','hostname')
    ftr_port = config.getint('fieldtrip','port')
    print 'Trying to connect to buffer on %s:%i ...' % (ftr_host, ftr_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftr_host, ftr_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

H = ftc.getHeader()
if debug>0:
    print 'Header loaded'

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

###### Parameters
channelY = config.getint('processing','channelY')-1 # one-offset in the ini file, zero-offset in the code
channelZ = config.getint('processing','channelZ')-1 # one-offset in the ini file, zero-offset in the code
window   = config.getfloat('processing','window')*H.fSample

channel_indx = []
channel_name = ['channelX', 'channelY', 'channelZ']
for chan in channel_name:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channel_indx.append(config.getint('processing',chan)-1)

while True:
    time.sleep(config.getfloat('general','delay'))

    H = ftc.getHeader()
    if H.nSamples < window:
        # there are not yet enough samples in the buffer
        pass

    # get the most recent data segment
    start = H.nSamples - int(window)
    stop  = H.nSamples-1
    dat   = ftc.getData([start,stop])

    # this is for debugging
    printval = []

    for chanstr,chanindx in zip(channel_name, channel_indx):

        # the scale option is channel specific
        if config.has_option('scale', chanstr):
            try:
                scale = config.getfloat('scale', chanstr)
            except:
                scale = r.get(config.get('scale', chanstr))
        else:
            scale = 1
        # the offset option is channel specific
        if config.has_option('offset', chanstr):
            try:
                offset = config.getfloat('offset', chanstr)
            except:
                offset = r.get(config.get('offset', chanstr))
        else:
            offset = 0

        # compute the mean over the window
        val = numpy.mean(dat[:,chanindx])
        # apply the scale and offset
        val = EEGsynth.rescale(val, scale, offset)

        # this is for debugging
        printval.append(val)

        r.set(config.get('output', 'prefix') + '.' + chanstr, val)

    if debug>1:
        print printval
