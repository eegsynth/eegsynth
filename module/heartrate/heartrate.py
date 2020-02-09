#!/usr/bin/env python

# This module detects heart beats and returns the rate based on the beat-to-beat interval
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
sys.path.insert(0, os.path.join(path,'../../lib'))
import FieldTrip
import EEGsynth

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
    debug = patch.getint('general','debug')

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
    global timeout, hdr_input, start, channel, window, threshold, lrate, debounce, key_beat, key_rate, curvemin, curvemean, curvemax, prev, begsample, endsample

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info('Waiting for data to arrive...')
        if (time.time()-start)>timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.info('Data arrived')
    monitor.debug(hdr_input)
    monitor.debug(hdr_input.labels)

    # get the options from the configuration file
    channel   = patch.getint('input','channel')-1                                 # one-offset in the ini file, zero-offset in the code
    window    = patch.getfloat('processing','window')
    threshold = patch.getfloat('processing', 'threshold')
    lrate     = patch.getfloat('processing', 'learning_rate', default=1)
    debounce  = patch.getfloat('processing', 'debounce', default=0.3)             # minimum time between beats (s)
    key_beat  = patch.getstring('output', 'heartbeat')
    key_rate  = patch.getstring('output', 'heartrate')

    window = round(window * hdr_input.fSample)  # in samples

    curvemin  = np.nan;
    curvemean = np.nan;
    curvemax  = np.nan;
    prev      = np.nan

    begsample = -1
    endsample = -1

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, channel, window, threshold, lrate, debounce, key_beat, key_rate, curvemin, curvemean, curvemax, prev, begsample, endsample
    global dat, negrange, posrange, thresh, prevsample, sample, last, bpm, duration, duration_scale, duration_offset

    monitor.loop()
    time.sleep(patch.getfloat('general','delay'))

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        raise RuntimeError("buffer reset detected")
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        monitor.info('Waiting for data to arrive...')
        return

    # process the last window
    begsample = hdr_input.nSamples - int(window)
    endsample = hdr_input.nSamples - 1
    dat       = ft_input.getData([begsample,endsample]).astype(np.double)
    dat       = dat[:,channel]

    if np.isnan(curvemin):
        curvemin  = np.min(dat)
        curvemean = np.mean(dat)
        curvemax  = np.max(dat)
    else:
        # the learning rate determines how fast the threshold auto-scales (0=never, 1=immediate)
        curvemin  = (1 - lrate) * curvemin  + lrate * np.min(dat)
        curvemean = (1 - lrate) * curvemean + lrate * np.mean(dat)
        curvemax  = (1 - lrate) * curvemax  + lrate * np.max(dat)

    # both are defined as positive
    negrange = curvemean - curvemin
    posrange = curvemax - curvemean

    if negrange>posrange:
        thresh = (curvemean - dat) > threshold * negrange
    else:
        thresh = (dat - curvemean) > threshold * posrange

    if not np.isnan(prev):
        prevsample = int(round(prev * hdr_input.fSample)) - begsample
        if prevsample>0 and prevsample<len(thresh):
            thresh[0:prevsample] = False

    # determine samples that are true and where the previous sample is false
    thresh = np.logical_and(thresh[1:], np.logical_not(thresh[0:-1]))
    sample = np.where(thresh)[0]+1

    if len(sample)<1:
        # no beat was detected
        return

    # determine the last beat in the window
    last = sample[-1]
    last = (last + begsample) / hdr_input.fSample

    if np.isnan(prev):
        # the first beat has not been detected yet
        prev = last
        return

    if last-prev>debounce:
        # require a minimum time between beats
        bpm  = 60./(last-prev)
        prev = last

        if not np.isnan(bpm):
            # this is to schedule a timer that switches the gate off
            duration        = patch.getfloat('general', 'duration', default=0.1)
            duration_scale  = patch.getfloat('scale', 'duration', default=1)
            duration_offset = patch.getfloat('offset', 'duration', default=0)
            duration        = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)

            patch.setvalue(key_rate, bpm)
            patch.setvalue(key_beat, bpm, duration=duration)

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
