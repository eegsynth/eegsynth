#!/usr/bin/env python

# This module maps a single control signal onto multiple bilinear mixed signals
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2018 EEGsynth project
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

import ConfigParser  # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import argparse
import math
import numpy as np
import os
import redis
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder,
                                                            os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# the input scale and offset are used to map the Redis values to internal values
input_scale = patch.getfloat('input', 'scale', default=1.)
input_offset = patch.getfloat('input', 'offset', default=0.)

# the output scale and offset are used to map the internal values to Redis values
output_scale = patch.getfloat('output', 'scale', default=1.)
output_offset = patch.getfloat('output', 'offset', default=0.)

# there can be any number of output channels
channel_item, channel_name = zip(*config.items('output'))
match = [str.startswith(key, 'channel') for key in channel_item]
# make a list of the output channels
channel_item = [c for (c, m) in zip(channel_item, match) if m]
channel_name = [c for (c, m) in zip(channel_name, match) if m]
nchannel = len(channel_item)

def even(val):
    return not(val % 2)

def clip01(val):
    return min(max(val,0),1)

dwelltime = 0.
segment = 0
previous = 'no'

while True:
    # measure the time that it takes
    start = time.time()

    # these can change on the fly
    delay = patch.getfloat('general', 'delay')
    switch_time = patch.getfloat('switch', 'time', default=1.0)
    switch_precision = patch.getfloat('switch', 'precision', default=0.1)
    switch_precision = EEGsynth.rescale(switch_precision, slope=input_scale, offset=input_offset)

    input = patch.getfloat('input', 'channel', default=np.NaN)
    input = EEGsynth.rescale(input, slope=input_scale, offset=input_offset)

    if switch_precision > 0:
        # the input value is scaled relative to the corners
        # so that the switching happens exactly at the corners and is not visible
        input = input * (1 + 2 * switch_precision) - switch_precision
        lower_treshold = 0
        upper_treshold = 1
    else:
        # the thresholds are scaled relative to the corners
        # so that the switching happens prior to reaching the corner
        lower_treshold = 0. - switch_precision
        upper_treshold = 1. + switch_precision

    if debug > 1:
        print '------------------------------------------------------------------'

    # is there a reason to change?
    if even(segment):
        # the direction is normal on the even segments
        if input > upper_treshold:
            change = 'up'
        elif input < lower_treshold:
            change = 'down'
        else:
            change = 'no'
    else:
        # the direction is opposite on the odd segments
        if input > upper_treshold:
            change = 'down'
        elif input < lower_treshold:
            change = 'up'
        else:
            change = 'no'

    # is there a desired change in the same direction as the previous?
    if change == 'no' or change != previous:
        dwelltime = 0
    else:
        dwelltime += delay
        if debug > 1:
            print 'dwelling for', dwelltime
    previous = change

    # is the dwelltime long enough?
    if dwelltime > switch_time:
        if change == 'up':
            # switch to the next segment
            segment += 1
        else:
            # switch to the previous segment
            segment -= 1
        if debug > 1:
            print 'switch to segment', segment

    channel_val = [0. for i in range(nchannel)]
    for this in range(nchannel):
        if (segment % nchannel) == this:
            next = (this + 1) % nchannel
            # the scaled input value needs to be clipped between 0 and 1
            if even(segment):
                channel_val[this] = 1. - clip01(input)
                channel_val[next] = clip01(input)
            else:
                channel_val[this] = clip01(input)
                channel_val[next] = 1. - clip01(input)

    for key, val in zip(channel_name, channel_val):
        r.set(key, val)

    if debug > 0:
        # print them all on a single line, this is Python 2 specific
        print('segment=%2d' % segment),
        for key, val in zip(channel_name, channel_val):
            print(' %s = %0.2f' % (key, val)),
        print ""  # force a newline

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = delay
    elapsed = time.time() - start
    naptime = desired - elapsed
    if naptime > 0:
        # this approximates the desired delay for each iteration
        time.sleep(naptime)
