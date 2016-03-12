#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import OSC          # see https://trac.v2.nl/wiki/pyOSC

# eegsynth/lib contains shared modules
sys.path.insert(0, '../../lib')
import EEGsynth

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'outputosc.ini'))

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

s = OSC.OSCClient()
s.connect((config.get('osc','address'), config.getint('osc','port')))

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
        try:
            val = r.get(key2)
            if val is None:
                val = config.getfloat('default', key1)
            else:
                val = float(val)

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
            if config.has_option('scale', key1):
                try:
                    scale = config.getfloat('scale', key1)
                    print 'redis = ', scale
                except:
                    scale = r.get(config.get('scale', key1))
            else:
                scale = 1
            # the offset option is channel specific
            if config.has_option('offset', key1):
                try:
                    offset = config.getfloat('offset', key1)
                    print 'redis = ', offset
                except:
                    offset = r.get(config.get('offset', key1))
            else:
                offset = 1
            # apply the scale and offset
            val = EEGsynth.rescale(val, scale, offset)

            print key1, key2, key3, val
            msg = OSC.OSCMessage(key3)
            msg.append(val)
            s.send(msg)
        except:
            # the value is neither present in redis, nor in the default section of the *.ini file
            pass
