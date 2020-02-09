#!/usr/bin/env python

# This module detects whether a signal exceeds a specified threshold
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
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth
import FieldTrip


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input

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

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.success('Connected to FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to FieldTrip buffer")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, rectify, invert, prefix, window, scale_threshold, offset_threshold, scale_interval, offset_interval, channels, previous, begsample, endsample

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info('Waiting for data to arrive...')
        if (time.time() - start) > timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.info('Data arrived')
    monitor.debug(hdr_input)
    monitor.debug(hdr_input.labels)

    # get the options from the configuration file
    rectify = patch.getint('processing', 'rectify', default=0)
    invert  = patch.getint('processing', 'invert', default=0)
    prefix  = patch.getstring('output', 'prefix')
    window  = patch.getfloat('processing', 'window')     # in seconds
    window  = round(window * hdr_input.fSample)          # in samples

    scale_threshold   = patch.getfloat('scale', 'threshold', default=1)
    offset_threshold  = patch.getfloat('offset', 'threshold', default=0)
    scale_interval    = patch.getfloat('scale', 'interval', default=1)
    offset_interval   = patch.getfloat('offset', 'interval', default=0)

    channels = patch.getint('input', 'channels', multiple=True)
    channels = [chan - 1 for chan in channels] # since python using indexing from 0 instead of 1

    previous = [-np.Inf] * len(channels)

    # jump to the end of the input stream
    if hdr_input.nSamples<window:
        begsample = 0
        endsample = window-1
    else:
        begsample = hdr_input.nSamples-window
        endsample = hdr_input.nSamples-1

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, rectify, invert, prefix, window, scale_threshold, offset_threshold, scale_interval, offset_interval, channels, previous, begsample, endsample
    global dat_input, threshold, interval, channel, maxind, maxval, sample, key

    monitor.loop()

    # determine when we start polling for available data
    start = time.time()

    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if (hdr_input.nSamples-1)<(endsample-window):
            raise RuntimeError("buffer reset detected")
        if (time.time()-start)>timeout:
            raise RuntimeError("timeout while waiting for data")

    # get the input data
    dat_input = ft_input.getData([begsample, endsample]).astype(np.double)

    monitor.debug("read from sample %d to %d" % (begsample, endsample))

    # rectify the data
    if rectify:
        dat_input = np.absolute(dat_input)

    # invert the data
    if invert:
        dat_input = -dat_input

    threshold = patch.getfloat('processing', 'threshold')
    threshold = EEGsynth.rescale(threshold, slope=scale_threshold, offset=offset_threshold)
    interval  = patch.getfloat('processing', 'interval', default=0)
    interval  = EEGsynth.rescale(interval, slope=scale_interval, offset=offset_interval)

    for channel in channels:
        maxind = np.argmax(dat_input[:,channel])
        maxval = dat_input[maxind,channel]
        sample = maxind+begsample
        if maxval>=threshold and (sample-previous[channel])>=(interval*hdr_input.fSample):
            key = "%s.channel%d" % (patch.getstring('output','prefix'), channel+1)
            patch.setvalue(key, float(maxval))
            previous[channel] = sample

    # increment the counters for the next loop
    begsample += window
    endsample += window

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, ft_input

    ft_input.disconnect()
    monitor.success('Disconnected from input FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
