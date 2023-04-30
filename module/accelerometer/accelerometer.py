#!/usr/bin/env python

# This module convert accelerometer data from an OpenBCI Cyton board into control signals
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
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, window, channel_items, channel_name, channel_indx, item, begsample, endsample

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.success("Connected to FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to FieldTrip buffer")

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.success("Waiting for data to arrive...")
        if (time.time() - start) > timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.success("Data arrived")
    monitor.info(hdr_input)
    monitor.info(hdr_input.labels)

    # get the processing parameters
    window = patch.getfloat('processing', 'window')
    window = int(window * hdr_input.fSample)  # expressed in samples

    channel_items = patch.config.items('input')
    channel_name = []
    channel_indx = []
    for item in channel_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        channel_name.append(item[0])                           # the channel name
        channel_indx.append(patch.getint('input', item[0]) - 1)  # the channel number

    begsample = -1
    endsample = -1


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, window, channel_items, channel_name, channel_indx, item, begsample, endsample
    global dat, channame, chanindx, key, val

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        raise RuntimeError("buffer reset detected")
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        monitor.success("Waiting for data...")
        return

    # get the most recent data segment
    begsample = hdr_input.nSamples - window
    endsample = hdr_input.nSamples - 1
    dat = ft_input.getData([begsample, endsample]).astype(np.double)

    for channame, chanindx in zip(channel_name, channel_indx):
        # compute the mean over the time window
        key = patch.getstring('output', 'prefix') + '.' + channame
        val = np.mean(dat[:, chanindx])
        patch.setvalue(key, val)


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
