#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import threading
import mido

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder,'../../lib'))
import EEGsynth

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general', 'debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

mididevice  = config.get('midi', 'device')
try:
    outputport  = mido.open_output(mididevice)
    if debug>0:
        print "Connected to MIDI output"
except:
    print "Error: cannot connect to MIDI output"
    exit()

# control values are only relevant when different from the previous value
previous_val = {}
for channel in range(1, 16):
    name = 'channel{}'.format(channel)
    previous_val[name] = None

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for channel in range(1, 16):
        # loop over the control values
        name = 'channel{}'.format(channel)
        val = EEGsynth.getfloat('input', name, config, r)
        if val is None:
            if debug>1:
                print name, 'not available'
            continue

        if config.get('limiter_compressor', 'enable')=='yes':
            # the limiter/compressor applies to all channels and must exist as float or redis key
            lo = EEGsynth.getfloat('limiter_compressor', 'lo', config, r)
            hi = EEGsynth.getfloat('limiter_compressor', 'hi', config, r)
            if lo is None or hi is None:
                if debug>1:
                    print "cannot apply limiter/compressor"
            else:
                # apply the limiter/compressor
                val = EEGsynth.limiter(val, lo, hi)

        # the scale option is channel specific
        scale = EEGsynth.getfloat('scale', name, config, r, default=1)
        # the offset option is channel specific
        offset = EEGsynth.getfloat('offset', name, config, r, default=0)

        # apply the scale and offset
        val = EEGsynth.rescale(val, slope=scale, offset=offset)

        # ensure that it is within limits
        val = EEGsynth.clip(val, lower=-8192, upper=8191)

        if debug>0:
            print name, val

        if val==previous_val[name]:
            continue # it should be skipped when identical to the previous value
        previous_val[name] = val

        # midi channels in the inifile are 1-16, in the code 0-15
        midichannel = channel-1
        msg = mido.Message('pitchwheel', pitch=int(val), channel=midichannel)
        if debug>1:
            print msg
        outputport.send(msg)
