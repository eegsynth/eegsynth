#!/usr/bin/env python

# Quantizer does chromatic quantification of Redis values for musical interfaces
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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

import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug = patch.getint('general','debug')

# the input scale and offset are used to map Redis values to internal values
input_scale  = patch.getfloat('input', 'scale', default=127)
input_offset = patch.getfloat('input', 'offset', default=0)
# the output scale and offset are used to map internal values to Redis values
output_scale  = patch.getfloat('output', 'scale', default=1./127)
output_offset = patch.getfloat('output', 'offset', default=0)

# get the input and output options
input_channel, input_name = list(map(list, list(zip(*config.items('input')))))
output_name, output_value = list(map(list, list(zip(*config.items('quantization')))))

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
    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    monitor.info('----------------------------------------')

    for channel, name in zip(input_channel, input_name):
        val = patch.getfloat('input', channel)
        if val is None:
            monitor.info(name, 'not found')
            pass
        else:
            # map the Redis values to the internally used values
            val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
            # look up the nearest index of the input_value vector
            monitor.info('%s = %g' % (name, val))
            idx = find_nearest_idx(input_value, val)
            for qname, qvalue in zip(output_name, output_value):
                key = '{}.{}'.format(name, qname)
                if idx<len(qvalue):
                    # look up the corresponding output value
                    val = qvalue[idx]
                else:
                    # take the last value from the output list
                    val = qvalue[-1]
                monitor.info('%s = %g' % (key, val))
                # map the internally used values to Redis values
                val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
                patch.setvalue(key, val)
