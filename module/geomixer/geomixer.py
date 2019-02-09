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

from __future__ import print_function

try:
    # Python 2
    import configparser as configparser
except ImportError:
    # Python 3
    import ConfigParser as configparser

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

# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print(key, "=", val)
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
delay = patch.getfloat('general', 'delay')
number = patch.getint('switch', 'number', default=3)
prefix = patch.getstring('output', 'prefix')

# the scale and offset are used to map the Redis values to internal values
scale_input      = patch.getfloat('scale', 'input', default=1.)
scale_time       = patch.getfloat('scale', 'time', default=1.)
scale_precision  = patch.getfloat('scale', 'precision', default=1.)
offset_input     = patch.getfloat('offset', 'input', default=0.)
offset_time      = patch.getfloat('offset', 'time', default=0.)
offset_precision = patch.getfloat('offset', 'precision', default=0.)

channel_name = []
for vertex in range(number):
    # each vertex of the geometry has an output value
    # the output names are like "geomixer.spectral.channel1.alpha.vertex1"
    channel_name.append('%s.%s.vertex%d' % (prefix, patch.getstring('input', 'channel'), vertex+1))

def even(val):
    return not(val % 2)

def clip01(val):
    return min(max(val,0),1)

dwelltime = 0.
edge = 0
previous = 'no'

while True:
    # measure the time that it takes
    start = time.time()

    # these can change on the fly
    switch_time = patch.getfloat('switch', 'time', default=1.0)
    switch_time = EEGsynth.rescale(switch_time, slope=scale_time, offset=offset_time)
    switch_precision = patch.getfloat('switch', 'precision', default=0.1)
    switch_precision = EEGsynth.rescale(switch_precision, slope=scale_precision, offset=offset_precision)
    show_change('time', switch_time)
    show_change('precision', switch_precision)

    # get the input value and scale between 0 and 1
    input = patch.getfloat('input', 'channel', default=np.NaN)
    input = EEGsynth.rescale(input, slope=scale_input, offset=offset_input)

    if switch_precision > 0:
        # the input value is scaled relative to the vertices
        # so that the switching happens exactly at the vertices and is not visible
        input = input * (1 + 2 * switch_precision) - switch_precision
        lower_treshold = 0
        upper_treshold = 1
    else:
        # the thresholds are scaled relative to the vertices
        # so that the switching happens prior to reaching the vertex
        lower_treshold = 0. - switch_precision
        upper_treshold = 1. + switch_precision

    if debug > 1:
        print('------------------------------------------------------------------')

    # is there a reason to change?
    if even(edge):
        # the direction is normal on the even edges
        if input > upper_treshold:
            change = 'up'
        elif input < lower_treshold:
            change = 'down'
        else:
            change = 'no'
    else:
        # the direction is opposite on the odd edges
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
            print('dwelling for', dwelltime)
    previous = change

    # is the dwelltime long enough?
    if dwelltime > switch_time:
        if change == 'up':
            # switch to the next edge
            edge += 1
        elif change == 'down':
            # switch to the previous edge
            edge -= 1
        # send the edge number as an integer value to Redis
        key = '%s.%s.edge' % (prefix, patch.getstring('input', 'channel'))
        patch.setvalue(key, edge)
        if debug > 1:
            print('switch to edge', edge)

    channel_val = [0. for i in range(number)]
    for this in range(number):
        if (edge % number) == this:
            next = (this + 1) % number
            # the scaled input value needs to be clipped between 0 and 1
            if even(edge):
                channel_val[this] = 1. - clip01(input)
                channel_val[next] = clip01(input)
            else:
                channel_val[this] = clip01(input)
                channel_val[next] = 1. - clip01(input)
        patch.setvalue(channel_name[this], channel_val[this])

    if debug > 0:
        # print them all on a single line, this is Python 2 specific
        print(('edge=%2d' % edge), end=' ')
        for key, val in zip(channel_name, channel_val):
            print((' %s = %0.2f' % (key, val)), end=' ')
        print('')  # force a newline

    # this is a short-term approach, estimating the sleep for every block
    # this code is shared between generatesignal, playback and playbackctrl
    desired = delay
    elapsed = time.time() - start
    naptime = desired - elapsed
    if naptime > 0:
        # this approximates the desired delay for each iteration
        time.sleep(naptime)
