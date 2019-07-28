#!/usr/bin/env python

# Compressor and expander module changes the dynamic range
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2019 EEGsynth project
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std
import configparser
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

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print("Error: cannot connect to redis server")
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')
delay = patch.getfloat('general', 'delay')                 # in seconds

prefix = patch.getstring('output', 'prefix')

# get the input options
input_name, input_variable = list(zip(*config.items('input')))

if debug>0:
    for name,variable in zip(input_name, input_variable):
        print("%s = %s" % (name, variable))

while True:
    time.sleep(patch.getfloat('general', 'delay'))

    if patch.getint('processing', 'enable', default=1):
        # the compressor/expander applies to all channels and must exist as float or redis key
        scale = patch.getfloat('scale', 'lo', default=1.)
        offset = patch.getfloat('offset', 'lo', default=0.)
        lo = patch.getfloat('processing', 'lo')
        lo = EEGsynth.rescale(lo, slope=scale, offset=offset)

        scale = patch.getfloat('scale', 'hi', default=1.)
        offset = patch.getfloat('offset', 'hi', default=0.)
        hi = patch.getfloat('processing', 'hi')
        hi = EEGsynth.rescale(hi, slope=scale, offset=offset)

        monitor.update('lo', lo)
        monitor.update('hi', hi)

        if lo is None or hi is None:
            if debug>1:
                print("cannot apply compressor/expander")
            continue

        for name,variable in zip(input_name, input_variable):
            scale = patch.getfloat('scale', name, default=1)
            offset = patch.getfloat('offset', name, default=0)
            val = patch.getfloat('input', name)

            if val==None:
                # the value is not present in redis, skip it
                continue

            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            val = EEGsynth.compress(val, lo, hi)

            key = prefix +  "." + variable
            patch.setvalue(key, val)
            monitor.update(key, val)
