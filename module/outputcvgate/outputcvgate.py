#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import serial
import sys
import os

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'outputcvgate.ini'))

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
    s = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)
    if debug>0:
        print "Connected to serial port"
except:
    print "Error: cannot connect to serial port"
    exit()

while True:
    time.sleep(config.get('general','delay'))

    for chanindx in range(1, 8):
        chanstr = "cv%d" % chanindx
        chanval = r.get(config.get('input', chanstr))
        if chanval is None:
            chanval = config.getfloat('default', chanstr)
        else:
            chanval = float(chanval)
	    chanval = chanval * config.getfloat('multiply', chanstr);

        if config.get('limiter_compressor', 'enable')=='yes':
            # the limiter/lo option applies to all channels and must exist as float or redis key
            try:
                lo = config.getfloat('limiter_compressor', 'lo')
            except:
                lo = r.get(config.get('limiter_compressor', 'lo'))
            # the limiter/hi option applies to all channels and must exist as float or redis key
            try:
                hi = config.getfloat('limiter_compressor', 'hi')
            except:
                hi = r.get(config.get('limiter_compressor', 'hi'))
            # apply the limiter
            val = EEGsynth.limiter(val, lo, hi)

        # the scale option is channel specific
        if config.has_option('scale', chanstr):
            try:
                scale = config.getfloat('scale', chanstr)
                print 'redis = ', scale
            except:
                scale = r.get(config.get('scale', chanstr))
        else:
            scale = 1
        # the offset option is channel specific
        if config.has_option('offset', chanstr):
            try:
                offset = config.getfloat('offset', chanstr)
                print 'redis = ', offset
            except:
                offset = r.get(config.get('offset', chanstr))
        else:
            offset = 1
        # apply the scale and offset
        val = EEGsynth.rescale(val, scale, offset)

        s.write('*c%dv%04d#' % (chanindx, chanval))

    for chanindx in range(1, 8):
        chanstr = "gate%d" % chanindx
        chanval = r.get(config.get('input', chanstr))
        if chanval is None:
            chanval = bool(config.getint('default', chanstr))
        else:
            chanval = bool(val)
        s.write('*g%dv%d#' % (chanindx, chanval))
