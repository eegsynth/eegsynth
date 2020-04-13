#!/usr/bin/env python

# This module maps a single control signal onto multiple bilinear mixed signals
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2020 EEGsynth project
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
import math
import numpy as np
import os
import redis
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
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


def even(val):
    return not(val % 2)


def clip01(val):
    return min(max(val, 0), 1)


def _setup():
    """Initialize the module
    This adds a set of global variables
    """
    global parser, args, config, r, response, patch

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    """Start the module
    This uses the global variables from setup and adds a set of global variables
    """
    global parser, args, config, r, response, patch, name
    global monitor, debug, stepsize, number, prefix, scale_input, scale_time, scale_precision, offset_input, offset_time, offset_precision, channel_name, vertex, dwelltime, edge, previous

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')
    stepsize = patch.getfloat('general', 'delay')
    number = patch.getint('switch', 'number', default=3)
    prefix = patch.getstring('output', 'prefix')

    # the scale and offset are used to map the Redis values to internal values
    scale_input = patch.getfloat('scale', 'input', default=1.)
    scale_time = patch.getfloat('scale', 'time', default=1.)
    scale_precision = patch.getfloat('scale', 'precision', default=1.)
    offset_input = patch.getfloat('offset', 'input', default=0.)
    offset_time = patch.getfloat('offset', 'time', default=0.)
    offset_precision = patch.getfloat('offset', 'precision', default=0.)

    channel_name = []
    for vertex in range(number):
        # each vertex of the geometry has an output value
        # the output names are like "geomixer.spectral.channel1.alpha.vertex1"
        channel_name.append('%s.%s.vertex%d' % (prefix, patch.getstring('input', 'channel'), vertex + 1))

    dwelltime = 0.
    edge = 0
    previous = 'no'

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global parser, args, config, r, response, patch
    global monitor, debug, stepsize, number, prefix, scale_input, scale_time, scale_precision, offset_input, offset_time, offset_precision, channel_name, vertex, dwelltime, edge, previous
    global switch_time, switch_precision, input, lower_treshold, upper_treshold, change, key, channel_val, this, next, val, desired, elapsed, naptime, s

    # these can change on the fly
    switch_time = patch.getfloat('switch', 'time', default=1.0)
    switch_time = EEGsynth.rescale(switch_time, slope=scale_time, offset=offset_time)
    switch_precision = patch.getfloat('switch', 'precision', default=0.1)
    switch_precision = EEGsynth.rescale(switch_precision, slope=scale_precision, offset=offset_precision)

    monitor.update('time', switch_time)
    monitor.update('precision', switch_precision)

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

    monitor.debug('------------------------------------------------------------------')

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
        dwelltime += stepsize
        monitor.debug('dwelling for ' + str(dwelltime))
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
        monitor.debug('switch to edge ' + str(edge))

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
        # construct a string with all details on a single line
        s = 'edge=%2d' % (edge)
        for key, val in zip(channel_name, channel_val):
            s += ' %s = %0.2f' % (key, val)
        monitor.info(s)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_forever():
    """Run the main loop forever
    """
    global monitor, stepsize
    while True:
        # measure the time to correct for the slip
        start = time.time()

        monitor.loop()
        _loop_once()

        # correct for the slip
        elapsed = time.time() - start
        naptime = stepsize - elapsed
        if naptime > 0:
            monitor.trace("naptime = " + str(naptime))
            time.sleep(naptime)



def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt
    """
    sys.exit()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
