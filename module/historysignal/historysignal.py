#!/usr/bin/env python

# This module computes descriptive statistics (min, max, etc.) from the recent signal history
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
import numpy as np
import os
import redis
import sys
import time
from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std

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
import FieldTrip


# see https://en.wikipedia.org/wiki/Median_absolute_deviation
def mad(arr, axis=None):
    if axis==1:
        val = np.apply_along_axis(mad, 1, arr)
    else:
        val = np.nanmedian(np.abs(arr - np.nanmedian(arr)))
    return val


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
        monitor.success('Connected to input FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to input FieldTrip buffer")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, inputlist, prefix, enable, stepsize, window, numhistory, numchannel, history, historic, begsample, endsample

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info('Waiting for data to arrive...')
        if (time.time()-start) > timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.debug("input nsample", hdr_input.nSamples)
    monitor.debug("input nchan", hdr_input.nChannels)

    # get the options from the configuration file
    inputlist   = patch.getint('input', 'channels', multiple=True)
    prefix      = patch.getstring('output', 'prefix')
    enable      = patch.getint('history', 'enable', default=1)
    stepsize    = patch.getfloat('history', 'stepsize')                 # in seconds
    window      = patch.getfloat('history', 'window')                   # in seconds

    stepsize    = int(round(hdr_input.fSample*stepsize))                # in samples
    numhistory  = int(round(hdr_input.fSample*window))                  # in samples
    numchannel  = len(inputlist)

    # this will contain the full list of historic values
    history = np.empty((numhistory, numchannel)) * np.NAN

    # this will contain the statistics of the historic values
    historic = {}

    # jump to the end of the input stream
    if hdr_input.nSamples<stepsize:
        begsample = 0
        endsample = stepsize-1
    else:
        begsample = hdr_input.nSamples-stepsize
        endsample = hdr_input.nSamples-1

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, inputlist, prefix, enable, stepsize, window, numhistory, numchannel, history, historic, begsample, endsample
    global prev_enable, dat_input, chanindx, operation, key, val

    monitor.loop()
    # determine the start of the actual processing
    start = time.time()

    # update the enable status
    prev_enable = enable
    enable = patch.getint('history', 'enable', default=1)

    if enable and prev_enable:
        monitor.info("Updating the history")
    elif enable and not prev_enable:
        monitor.info("Enabling the updating")
        # jump to the end of the input stream
        hdr_input = ft_input.getHeader()
        begsample = hdr_input.nSamples-stepsize
        endsample = hdr_input.nSamples-1
    elif not enable and not prev_enable:
        monitor.info("Not updating the history")
    elif not enable and prev_enable:
        monitor.info("Disabling the updating")

    if not enable:
        time.sleep(patch.getfloat('general', 'delay'))
        return

    while endsample > hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if hdr_input.nSamples < begsample:
            raise RuntimeError("buffer reset detected")
        if (time.time()-start) > timeout:
            raise RuntimeError("timeout while waiting for data")

    monitor.debug("reading samples", begsample, "to", endsample)

    # get the input data, sample vector and time vector
    dat_input = ft_input.getData([begsample, endsample]).astype(np.double)

    # shift the history and insert the most recent data
    history = np.roll(history, stepsize, axis=0)
    chanindx = np.asarray(inputlist,np.int32)-1
    history[-stepsize:,] = dat_input[:,chanindx]

    # compute some statistics
    historic['mean']    = np.nanmean(history.flatten(), axis=0)
    historic['std']     = np.nanstd(history.flatten(), axis=0)
    historic['min']     = np.nanmin(history.flatten(), axis=0)
    historic['max']     = np.nanmax(history.flatten(), axis=0)
    historic['range']   = historic['max'] - historic['min']

    if False:
        # use some robust estimators
        historic['median']  = np.nanmedian(history.flatten(), axis=0)
        # see https://en.wikipedia.org/wiki/Median_absolute_deviation
        historic['mad']     = mad(history.flatten(), axis=0)
        # for a normal distribution the 16th and 84th percentile correspond to the mean plus-minus one standard deviation
        historic['p03']     = np.percentile(history.flatten(),  3, axis=0) # mean minus 2x standard deviation
        historic['p16']     = np.percentile(history.flatten(), 16, axis=0) # mean minus 1x standard deviation
        historic['p84']     = np.percentile(history.flatten(), 84, axis=0) # mean plus 1x standard deviation
        historic['p97']     = np.percentile(history.flatten(), 97, axis=0) # mean plus 2x standard deviation
        # see https://en.wikipedia.org/wiki/Interquartile_range
        historic['iqr']     = historic['p84'] - historic['p16']

    for operation in list(historic.keys()):
        key = prefix + "." + operation
        val = historic[operation]
        patch.setvalue(key, val, debug > 1)

    begsample += stepsize
    endsample += stepsize

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
