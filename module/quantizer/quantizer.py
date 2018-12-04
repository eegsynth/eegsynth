#!/usr/bin/env python

# Quantizer does chromatic quantification of Redis values for musical interfaces
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# the input scale and offset are used to map Redis values to internal values
input_scale  = patch.getfloat('input', 'scale', default=127)
input_offset = patch.getfloat('input', 'offset', default=0)
# the output scale and offset are used to map internal values to Redis values
output_scale  = patch.getfloat('output', 'scale', default=0.00787401574803149606)
output_offset = patch.getfloat('output', 'offset', default=0)

# get the input and output options
input_channel, input_name = map(list, zip(*config.items('input')))
output_name, output_value = map(list, zip(*config.items('quantization')))

# remove the scale and offset from the input list
del input_channel[input_channel.index('scale')]
del input_channel[input_channel.index('offset')]

# get the list of values for each of the input values for quantization
for i,name in enumerate(output_name):
    output_value[i] = patch.getfloat('quantization', name, multiple=True)

# find the input value to which the data is to be quantized
index       =  output_name.index('value')
input_value =  output_value[index]
# remove the value from the output list
del output_name[index]
del output_value[index]

def find_nearest_idx(array,value):
    # find the index of the array element that is the nearest to the value
    idx = (np.abs(np.asarray(array)-value)).argmin()
    return idx

while True:
    time.sleep(patch.getfloat('general', 'delay'))

    if debug>0:
        print '----------------------------------------'

    for channel, name in zip(input_channel, input_name):
        val = patch.getfloat('input', channel)
        if val is None:
            if debug>0:
                print name, 'not found'
            pass
        else:
            # map the Redis values to the internally used values
            val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
            # look up the nearest index of the input_value vector
            if debug>0:
                print name, '=', val
            idx = find_nearest_idx(input_value, val)
            for qname, qvalue in zip(output_name, output_value):
                key = '{}.{}'.format(name, qname)
                if idx<len(qvalue):
                    # look up the corresponding output value
                    val = qvalue[idx]
                else:
                    # take the last value from the output list
                    val = qvalue[-1]
                if debug>0:
                    print key, '=', val
                # map the internally used values to Redis values
                val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
                patch.setvalue(key, val)
