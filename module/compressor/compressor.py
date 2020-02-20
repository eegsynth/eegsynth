#!/usr/bin/env python

# Compressor and expander module changes the dynamic range
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
sys.path.insert(0,os.path.join(path, '../../lib'))
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
debug   = patch.getint('general', 'debug')
delay   = patch.getfloat('general', 'delay')
prefix  = patch.getstring('output', 'prefix')

# get the input options
input_name, input_variable = list(zip(*config.items('input')))

for name,variable in zip(input_name, input_variable):
    monitor.info("%s = %s" % (name, variable))

while True:
    monitor.loop()
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
            monitor.debug("cannot apply compressor/expander")
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
