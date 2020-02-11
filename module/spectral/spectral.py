#!/usr/bin/env python

# Spectral outputs power envelopes of user-defined frequency bands
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
from scipy.signal import detrend

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
    global parser, args, config, r, response, patch, monitor, ft_host, ft_port, ft_input

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

    try:
        ft_host = patch.getstring('fieldtrip','hostname')
        ft_port = patch.getint('fieldtrip','port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.info("Connected to FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to FieldTrip buffer")


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, channel_items, channame, chanindx, item, prefix, begsample, endsample

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info("Waiting for data to arrive...")
        if (time.time()-start)>timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.info("Data arrived")
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

    prefix = patch.getstring('output', 'prefix')

    begsample = -1
    endsample = -1


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, channel_items, channame, chanindx, item, prefix, begsample, endsample
    global scale_window, offset_window, window, taper, frequency, band_items, bandname, bandlo, bandhi, lohi, dat, power, chan, band, meandat, sample, F, i, lo, hi, count, key

    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    scale_window = patch.getfloat('scale', 'window', default=1.)
    offset_window = patch.getfloat('offset', 'window', default=0.)
    window = patch.getfloat('processing', 'window', default=2)
    window = EEGsynth.rescale(window, slope=scale_window, offset=offset_window)

    monitor.update('window', window)

    window = int(round(window * hdr_input.fSample))  # in samples
    taper = np.hanning(window)
    frequency = np.fft.rfftfreq(window, 1.0 / hdr_input.fSample)

    band_items = config.items('band')
    bandname = []
    bandlo   = []
    bandhi   = []
    for item in band_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        lohi = patch.getfloat('band', item[0], multiple=True)
        bandname.append(item[0])
        bandlo.append(lohi[0])
        bandhi.append(lohi[1])

    monitor.debug(bandname, bandlo, bandhi)

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        raise RuntimeError("buffer reset detected")
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        monitor.info("Waiting for data...")
        return

    # get the most recent data segment
    begsample = hdr_input.nSamples - window
    endsample = hdr_input.nSamples - 1
    dat = ft_input.getData([begsample, endsample]).astype(np.double)
    dat = dat[:, chanindx]

    # demean the data to prevent spectral leakage
    dat = detrend(dat, axis=0, type='constant')

    # taper the data
    dat = dat * taper[:, np.newaxis]

    # compute the FFT over the sample direction
    F = np.fft.rfft(dat, axis=0)

    power = [0] * len(channame) * len(bandname)
    i = 0
    for chan in range(F.shape[1]):
        for lo,hi in zip(bandlo,bandhi):
            power[i] = 0
            count = 0
            for sample in range(len(frequency)):
                if frequency[sample]>=lo and frequency[sample]<=hi:
                    power[i] += abs(F[sample, chan]*F[sample, chan])
                    count    += 1
            if count>0:
                power[i] /= count
            i+=1

    monitor.debug(power)

    i = 0
    for chan in channame:
        for band in bandname:
            key = "%s.%s.%s" % (prefix, chan, band)
            patch.setvalue(key, power[i])
            i+=1


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
