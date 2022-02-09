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
# from numpy import random
from scipy.stats import binom, norm

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


def trigger(send=True):
    global patch, t, lock, baserate, burstprob, burstrate, spread, burst, triggerindx, jitterlist, valuelist, typelist, val

    if send:
        # send the current trigger if there is a value
        key = patch.getstring('output', 'prefix') + '.note'
        patch.setvalue(key, val)

    # with lock:

    # add new upcoming dt(s)

    if triggerindx > len(jitterlist)-1:


        # add bursts
        if np.random.random() < burstprob and triggerindx > 0:

            # add n number of triggers from normal distribution
            nrtriggers = binom.rvs(n=5, p=0.2, size=1) + 1
            jitter = norm.rvs(size=nrtriggers, loc=1, scale=0.1)  # can be different from base jitter
            jitterlist.extend(jitter)
            temp = np.repeat(valuelist[triggerindx-1], nrtriggers)
            valuelist.extend(temp)
            typelist.extend(np.repeat(1, len(jitter)))
            monitor.debug('Adding burst with intervals:', jitter)

            # then add time-corrected interval to keep rhythm, corrected if burst lasted beyond single beat
            jitter = norm.rvs(size=1, loc=1, scale=0.1)  # scale = std, is 10% of baserate
            jitterlist.append(jitter[0])
            valuelist.append(np.random.random())
            typelist.append(0)
        else:

            # add regular single trigger
            jitter = norm.rvs(size=1, loc=1, scale=0.1)  # scale = std, is 10% of baserate
            jitterlist.append(jitter[0])
            valuelist.append(np.random.random())
            typelist.append(0)

    if typelist[triggerindx] == 0:
        dt = (60 / baserate) * jitterlist[triggerindx]
    else:
        dt = (60 / burstrate) * jitterlist[triggerindx]
    if dt < 0.05:
        dt = 0.05

    monitor.debug('basetime = %f' % (60 / baserate))
    monitor.debug('jitter = %f' % jitterlist[triggerindx])
    monitor.debug('scheduling next trigger after %g seconds' % dt)
    val = valuelist[triggerindx]

    triggerindx += 1
    print(np.cumsum(typelist))
    print(np.cumsum(typelist) > 9)

    # if repeat locked
    if sum(typelist[:triggerindx]) >= 4:
        triggerindx = 0

    t = threading.Timer(dt, trigger)
    t.start()


def _setup():
    """Initialize the module
    This adds a set of global variables
    """
    global parser, args, config, r, response, patch

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'),
                        help="name of the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0,
                              charset='utf-8', decode_responses=True)
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
    global monitor, debug, scale_rate, scale_spread, offset_rate, offset_spread, baserate, spread, lock, t
    global burstprob, burstrate, scale_burstprob, offset_burstprob, scale_burstrate, offset_burstrate
    global triggerindx, jitterlist, valuelist, typelist, val

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    # the scale and offset are used to map the Redis values to internal values
    scale_rate = patch.getfloat('scale', 'baserate', default=1)
    scale_spread = patch.getfloat('scale', 'spread', default=1)
    scale_burstprob = patch.getfloat('scale', 'burstprob', default=1)
    scale_burstrate = patch.getfloat('scale', 'burstrate', default=1)
    offset_rate = patch.getfloat('offset', 'baserate', default=0)
    offset_spread = patch.getfloat('offset', 'spread', default=0)
    offset_burstprob = patch.getfloat('offset', 'burstprob', default=0)
    offset_burstrate = patch.getfloat('offset', 'burstrate', default=0)

    # read them once, they will be constantly updated in the main loop
    baserate = patch.getfloat('interval', 'baserate', default=60)
    spread = patch.getfloat('interval', 'spread', default=10)
    burstprob = patch.getfloat('interval', 'burstprob', default=0)
    burstrate = patch.getfloat('interval', 'burstrate', default=60)
    baserate = EEGsynth.rescale(baserate, slope=scale_rate, offset=offset_rate)
    spread = EEGsynth.rescale(spread, slope=scale_spread, offset=offset_spread)
    burstprob = EEGsynth.rescale(burstprob, slope=scale_burstprob, offset=offset_burstprob)
    burstrate = EEGsynth.rescale(burstrate, slope=scale_burstrate, offset=offset_burstrate)

    # start with empty list and index = 0, list will be created in loop
    triggerindx = 0
    jitterlist = []
    valuelist = []
    typelist = []
    val = 0
    # jitterlist.append(1)

    # this is to prevent the trigger function from accessing the parameters while they are being updated
    lock = threading.Lock()

    # make an initial timer object, this is needed in case parameters are updated prior to the execution of the first trigger
    t = threading.Timer(0, None)

    # start the chain of triggers, the first one does not have to be sent
    trigger(send=False)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global parser, args, config, r, response
    global patch, monitor, debug, scale_rate, scale_spread, offset_rate, offset_spread, baserate, spread, lock, t
    global change
    global burstprob, burstrate, scale_burstprob, scale_burstrate, offset_burstprob, offset_burstrate
    # global triggerindx, jitterlist, valuelist

    with lock:
        baserate = patch.getfloat('interval', 'baserate', default=60)
        spread = patch.getfloat('interval', 'spread', default=10)
        baserate = EEGsynth.rescale(baserate, slope=scale_rate, offset=offset_rate)
        spread = EEGsynth.rescale(spread, slope=scale_spread, offset=offset_spread)
        burstprob = patch.getfloat('interval', 'burstprob', default=0)
        burstrate = patch.getfloat('interval', 'burstrate', default=60)
        burstprob = EEGsynth.rescale(burstprob, slope=scale_burstprob, offset=offset_burstprob)
        burstrate = EEGsynth.rescale(burstrate, slope=scale_burstrate, offset=offset_burstrate)

    change = monitor.update('baserate', baserate)
    change = monitor.update('spread', spread) or change
    change = monitor.update('burstprob', burstprob)
    change = monitor.update('burstrate', burstrate) or change

    # if change:
    #     monitor.debug('canceling previously scheduled trigger')
    #     t.cancel()
    #     trigger(send=False)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_forever():
    """Run the main loop forever
    """
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt
    """
    sys.exit()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
