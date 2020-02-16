#!/usr/bin/env python

# Complexity measures computed per channel over a sliding window
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
import math
import multiprocessing
import numpy as np
import os
import redis
import sys
import threading
import time

try:
    # Neurokit is a rather large Python package with a lot of extra dependencies.
    # It is only used inside this specific EEGsynth module, hence it is not installed automatically
    from neurokit.signal import complexity
except ImportError:
    # give a warning, not an error, so that eegsynth.py does not fail as a whole
    print('Warning: neurokit is required for the complexity module, please install it with "pip install neurokit"')

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
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
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
        ft_host = patch.getstring('fieldtrip','hostname')
        ft_port = patch.getint('fieldtrip','port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.success('Connected to FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to FieldTrip buffer")


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, channel_items, channame, chanindx, item, shannon, sampen, multiscale, spectral, svd, correlation, higushi, petrosian, fisher, hurst, dfa, lyap_r, lyap_e, window, taper, frequency, begsample, endsample

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

    channel_items = config.items('input')
    channame = []
    chanindx = []
    for item in channel_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        channame.append(item[0])
        chanindx.append(patch.getint('input', item[0])-1)

    monitor.info(channame, chanindx)

    shannon     = patch.getint('metrics', 'shannon',     default=0) != 0
    sampen      = patch.getint('metrics', 'sampen',      default=0) != 0
    multiscale  = patch.getint('metrics', 'multiscale',  default=0) != 0
    spectral    = patch.getint('metrics', 'spectral',    default=0) != 0
    svd         = patch.getint('metrics', 'svd',         default=0) != 0
    correlation = patch.getint('metrics', 'correlation', default=0) != 0
    higushi     = patch.getint('metrics', 'higushi',     default=0) != 0
    petrosian   = patch.getint('metrics', 'petrosian',   default=0) != 0
    fisher      = patch.getint('metrics', 'fisher',      default=0) != 0
    hurst       = patch.getint('metrics', 'hurst',       default=0) != 0
    dfa         = patch.getint('metrics', 'dfa',         default=0) != 0
    lyap_r      = patch.getint('metrics', 'lyap_r',      default=0) != 0
    lyap_e      = patch.getint('metrics', 'lyap_e',      default=0) != 0
    window      = patch.getfloat('processing','window')  # in seconds

    window      = int(round(window * hdr_input.fSample)) # in samples
    taper       = np.hanning(window)
    frequency   = np.fft.rfftfreq(window, 1.0/hdr_input.fSample)

    monitor.trace('taper     = ', taper)
    monitor.trace('frequency = ', frequency)

    begsample = -1
    endsample = -1


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, channel_items, channame, chanindx, item, shannon, sampen, multiscale, spectral, svd, correlation, higushi, petrosian, fisher, hurst, dfa, lyap_r, lyap_e, window, taper, frequency, begsample, endsample
    global dat, meandat, chan, sample, metrics, timeseries, metric_names, metric, shortmetric, key, val

    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        raise RuntimeError("buffer reset detected")
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        monitor.info('Waiting for data to arrive...')
        return

    # get the most recent data segment
    begsample = hdr_input.nSamples - window
    endsample = hdr_input.nSamples - 1
    dat = ft_input.getData([begsample, endsample]).astype(np.double)
    dat = dat[:, chanindx]

    # subtract the channel mean and apply the taper to each sample
    meandat = dat.mean(0)
    for chan in range(dat.shape[1]):
        for sample in range(dat.shape[0]):
            dat[sample, chan] -= meandat[chan]
            dat[sample, chan] *= taper[sample]

    # compute complexity over the sample direction
    metrics = []
    for timeseries in dat.T:
        metrics.append(complexity(timeseries,
                        sampling_rate=hdr_input.fSample,
                        shannon=shannon,
                        sampen=sampen,
                        multiscale=multiscale,
                        spectral=spectral,
                        svd=svd,
                        correlation=correlation,
                        higushi=higushi,
                        petrosian=petrosian,
                        fisher=fisher,
                        hurst=hurst,
                        dfa=dfa,
                        lyap_r=lyap_r,
                        lyap_e=lyap_e,
                        ))

    metric_names = list(metrics[0].keys())

    for chan in chanindx:
        for metric in metric_names:
            shortmetric = metric.lower()
            # remove some trailing information
            if shortmetric.startswith('entropy_'):
                shortmetric = shortmetric[len('entropy_'):]
            if shortmetric.startswith('fractal_dimension_'):
                shortmetric = shortmetric[len('fractal_dimension_'):]
            key = "{}.{}".format(channame[chan], shortmetric)
            val = metrics[chan][metric]
            patch.setvalue(key, val)
            monitor.update(key, val)


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
