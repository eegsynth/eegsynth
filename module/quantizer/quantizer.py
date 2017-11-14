#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
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

# get the input and output options
input_channel, input_name = map(list, zip(*config.items('input')))
quantized_name, quantized_value = map(list, zip(*config.items('quantization')))

# get the list of values for each of the quantization levels
for i,name in enumerate(quantized_name):
    quantized_value[i] = EEGsynth.getfloat('quantization', name, config, r, multiple=True)

# find the level to which the data is to be quantized
index =  quantized_name.index('level')
level =  quantized_value[index]
# remove the level from the list
del quantized_name[index]
del quantized_value[index]

def find_nearest_idx(array,value):
    # find the index of the array element that is the nearest to the value
    idx = (np.abs(np.asarray(array)-value)).argmin()
    return idx

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for channel,name in zip(input_channel, input_name):
        val = EEGsynth.getfloat('input', channel, config, r)
        if val is None:
            pass
        else:
            idx = find_nearest_idx(level, val)
            for qname, qvalue in zip(quantized_name, quantized_value):
                key = '{}.{}'.format(name, qname)
                val = qvalue[idx]
                if debug>1:
                    print key, '=', val
                r.set(key, val)             # send it as control value
