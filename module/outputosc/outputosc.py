#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import OSC          # see https://trac.v2.nl/wiki/pyOSC
import argparse
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
    s = OSC.OSCClient()
    s.connect((config.get('osc','hostname'), config.getint('osc','port')))
    if debug>0:
        print "Connected to OSC server"
except:
    print "Error: cannot connect to OSC server"
    exit()

# keys should be present in both the input and output section of the *.ini file
list_input  = config.items('input')
list_output = config.items('output')

list1 = [] # the key name that matches in the input and output section of the *.ini file
list2 = [] # the key name in REDIS
list3 = [] # the key name in OSC
for i in range(len(list_input)):
    for j in range(len(list_output)):
        if list_input[i][0]==list_output[j][0]:
            list1.append(list_input[i][0])
            list2.append(list_input[i][1])
            list3.append(list_output[j][1])

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for key1,key2,key3 in zip(list1,list2,list3):

        val = EEGsynth.getfloat('input', key1, config, r, multiple=True )
        if any(item is None for item in val):
            # the control value is not present in redis, skip it
            continue
        else:
            val = [float(x) for x in val]

        if EEGsynth.getint('compressor_expander', 'enable', config, r):
            # the compressor applies to all channels and must exist as float or redis key
            lo = EEGsynth.getfloat('compressor_expander', 'lo', config, r)
            hi = EEGsynth.getfloat('compressor_expander', 'hi', config, r)
            if lo is None or hi is None:
                if debug>1:
                    print "cannot apply compressor/expander"
            else:
                # apply the compressor/expander
                val = EEGsynth.compress(val, lo, hi)

        # the scale option is channel specific
        scale = EEGsynth.getfloat('scale', key1, config, r, default=1)
        # the offset option is channel specific
        offset = EEGsynth.getfloat('offset', key1, config, r, default=0)
        # apply the scale and offset
        val = EEGsynth.rescale(val, slope=scale, offset=offset)

        if debug>1:
            print 'OSC message', key3, '=', val

        msg = OSC.OSCMessage(key3)
        msg.append(val)
        s.send(msg)
