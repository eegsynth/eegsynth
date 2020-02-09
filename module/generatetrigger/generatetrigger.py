#!/usr/bin/env python

# Generatetrigger generates triggers at random intervals and sends them to Redis
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
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
import threading
from numpy import random

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
sys.path.insert(0, os.path.join(path, '../../lib'))
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
debug = patch.getint('general', 'debug')

# the scale and offset are used to map the Redis values to internal values
scale_rate     = patch.getfloat('scale', 'rate', default=1)
scale_spread   = patch.getfloat('scale', 'spread', default=1)
offset_rate    = patch.getfloat('offset', 'rate', default=0)
offset_spread  = patch.getfloat('offset', 'spread', default=0)

# read them once, they will be constantly updated in the main loop
rate   = patch.getfloat('interval', 'rate', default=60)
spread = patch.getfloat('interval', 'spread', default=10)
rate   = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
spread = EEGsynth.rescale(spread, slope=scale_spread, offset=offset_spread)

# make an initial timer object, this is needed in case parameters are updated prior to the execution of the first trigger
t = threading.Timer(0, None)

def trigger(send=True):
    global t
    if send:
        # send the current trigger
        key = patch.getstring('output', 'prefix') + '.note'
        patch.setvalue(key, 1.)

    # the rate is in bpm, i.e. quarter notes per minute
    if rate-spread>0:
        mintime = 60/(rate-spread)
    else:
        mintime = 0
    mintime = max(mintime, patch.getfloat('general', 'delay')) # it should have at least some miminum time
    if rate+spread>0:
        maxtime = 60/(rate+spread)
    else:
        maxtime = 0
    maxtime = max(maxtime, patch.getfloat('general', 'delay')) # it should have at least some miminum time
    # compute a random duration which is uniform between mintime and maxtime
    duration = mintime + float(random.rand(1)) * (maxtime-mintime)
    # schedule the next trigger
    monitor.debug('scheduling next trigger after %g seconds' % (duration))
    t = threading.Timer(duration, trigger)
    t.start()


# start the chain of triggers, the first one does not have to be sent
trigger(send=False)

while True:
    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    rate   = patch.getfloat('interval', 'rate', default=60)
    spread = patch.getfloat('interval', 'spread', default=10)
    rate   = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
    spread = EEGsynth.rescale(spread, slope=scale_spread, offset=offset_spread)

    change = monitor.update('rate', rate)
    change = monitor.update('spread', spread) or change

    if change:
        monitor.debug('canceling previously scheduled trigger')
        t.cancel()
        trigger(send=False)
