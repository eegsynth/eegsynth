#!/usr/bin/env python

# Spectral outputs power envelopes of user-defined frequency bands
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2022 EEGsynth project
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

import numpy as np
import os
import sys
import time
from scipy.signal import detrend

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
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
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, channel_items, channame, chanindx, item, prefix, output, begsample, endsample

    try:
        ft_host = patch.getstring('fieldtrip','hostname')
        ft_port = patch.getint('fieldtrip','port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.info("Connected to FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to FieldTrip buffer")

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

    channel_items = patch.config.items('input')
    channame = []
    chanindx = []
    for item in channel_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        channame.append(item[0])
        chanindx.append(patch.getint('input', item[0])-1)

    monitor.info(str(channame) + " " + str(chanindx))

    prefix = patch.getstring('output', 'prefix')
    output = patch.getstring('processing', 'output', default='amplitude')  # amplitude, power or db

    begsample = -1
    endsample = -1


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, channel_items, channame, chanindx, item, prefix, output, begsample, endsample
    global scale_window, offset_window, window, taper, frequency, band_items, bandname, bandlo, bandhi, lohi, dat, power, chan, band, meandat, sample, F, i, lo, hi, count, key

    scale_window = patch.getfloat('scale', 'window', default=1.)
    offset_window = patch.getfloat('offset', 'window', default=0.)
    window = patch.getfloat('processing', 'window', default=2)
    window = EEGsynth.rescale(window, slope=scale_window, offset=offset_window)

    monitor.update('window', window)

    window = int(round(window * hdr_input.fSample))  # in samples
    taper = np.hanning(window)
    frequency = np.fft.fftfreq(window, 1.0 / hdr_input.fSample)

    band_items = patch.config.items('band')
    bandname = []
    bandlo   = []
    bandhi   = []
    for item in band_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        lohi = patch.getfloat('band', item[0], multiple=True, default=[0,hdr_input.fSample/2])
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
    if output == 'amplitude':
        F = abs(np.fft.fft(dat, axis=0))
    elif output == 'power':
        F = abs(np.fft.fft(dat, axis=0))**2
    elif output == 'db':
        F = 10*np.log10(abs(np.fft.fft(dat, axis=0)))

    # this vector contains the spectral estimate for each channel and frequency band
    value = [np.nan] * len(channame) * len(bandname)

    i = 0
    for lo,hi in zip(bandlo,bandhi):
        freqindx = np.logical_and(frequency>=lo, frequency<=hi)
        for chan in range(F.shape[1]):
            if freqindx.sum()>0:
                value[i] = np.mean(F[freqindx, chan])
            i+=1
    
    monitor.debug(np.around(value))

    i = 0
    for band in bandname:
        for chan in channame:
            key = "%s.%s.%s" % (prefix, chan, band)
            patch.setvalue(key, value[i])
            i+=1


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, ft_input
    ft_input.disconnect()
    monitor.success('Disconnected from input FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
