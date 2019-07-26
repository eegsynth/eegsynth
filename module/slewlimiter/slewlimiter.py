#!/usr/bin/env python

# Slew limiter for control channels
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2019 EEGsynth project
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
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print("Error: cannot connect to redis server")
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
prefix = patch.getstring('output', 'prefix')

# get the list of input variables
input_name, input_variable = list(map(list, list(zip(*config.items('input')))))

# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print("%s = %g" % (key, val))
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}

previous_val = {}
for name in input_name:
    previous_val[name] = None

while True:
    time.sleep(patch.getfloat('general', 'delay'))
    lrate = patch.getfloat('processing', 'learning_rate', default=1)

    for name, variable in zip(input_name, input_variable):
        key = '%s.%s' % (prefix, variable)
        val = patch.getfloat('input', name)
        if val is None:
            continue # it should be skipped when not present in the ini or Redis
        scale   = patch.getfloat('scale', name, default=1)
        offset  = patch.getfloat('offset', name, default=0)
        val = EEGsynth.rescale(val, slope=scale, offset=offset)
        if previous_val[name] is None:
            # initialize for the first time
            previous_val[name] = val
        val = (1 - lrate) * previous_val[name] + lrate * val
        if debug>0:
            show_change(key, val)
        patch.setvalue(key, val)
        previous_val[name] = val
