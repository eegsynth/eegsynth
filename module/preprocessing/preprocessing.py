#!/usr/bin/env python

# Preprocessing performs basic signal processing to data in a FieldTrip buffer,
# and puts this in a second FieldTrip buffer for further processing.
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
import redis
import argparse
import os
import sys
import time
import numpy as np
from copy import copy
from numpy.matlib import repmat

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

def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input, ft_output

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
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    try:
        ft_host = patch.getstring('input_fieldtrip','hostname')
        ft_port = patch.getint('input_fieldtrip','port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.info("Connected to input FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to input FieldTrip buffer")

    try:
        ft_host = patch.getstring('output_fieldtrip','hostname')
        ft_port = patch.getint('output_fieldtrip','port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.info("Connected to output FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input, ft_output
    global timeout, hdr_input, start, window, downsample, differentiate, integrate, rectify, smoothing, reference, default_scale, scale_lowpass, scale_highpass, scale_notchfilter, offset_lowpass, offset_highpass, offset_notchfilter, scale_filterorder, scale_notchquality, offset_filterorder, offset_notchquality, previous, differentiate_zi, integrate_zi, begsample, endsample

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('input_fieldtrip', 'timeout', default=30)

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

    window = patch.getfloat('processing', 'window')
    window = int(round(window*hdr_input.fSample))

    # Processing init
    downsample      = patch.getint('processing', 'downsample', default=None)
    differentiate   = patch.getint('processing', 'differentiate', default=0)
    integrate       = patch.getint('processing', 'integrate', default=0)
    rectify         = patch.getint('processing', 'rectify', default=0)
    downsample      = patch.getint('processing', 'downsample', default=None)
    smoothing       = patch.getfloat('processing', 'smoothing', default=None)
    reference       = patch.getstring('processing','reference')

    try:
        float(config.get('processing', 'highpassfilter'))
        float(config.get('processing', 'lowpassfilter'))
        float(config.get('processing', 'notchfilter'))
        # the filter frequencies are specified as numbers
        default_scale = 1.
    except:
        # the filter frequencies are specified as Redis channels
        # scale them to the Nyquist frequency
        default_scale = hdr_input.fSample/2

    monitor.info('default scale for filter settings is %.0f' % (default_scale))

    scale_lowpass       = patch.getfloat('scale', 'lowpassfilter', default=default_scale)
    scale_highpass      = patch.getfloat('scale', 'highpassfilter', default=default_scale)
    scale_notchfilter   = patch.getfloat('scale', 'notchfilter', default=default_scale)
    offset_lowpass      = patch.getfloat('offset', 'lowpassfilter', default=0)
    offset_highpass     = patch.getfloat('offset', 'highpassfilter', default=0)
    offset_notchfilter  = patch.getfloat('offset', 'notchfilter', default=0)

    scale_filterorder   = patch.getfloat('scale', 'filterorder', default=1)
    scale_notchquality  = patch.getfloat('scale', 'notchquality', default=1)
    offset_filterorder  = patch.getfloat('offset', 'filterorder', default=0)
    offset_notchquality = patch.getfloat('offset', 'notchquality', default=0)

    if downsample == None:
        ft_output.putHeader(hdr_input.nChannels, hdr_input.fSample, FieldTrip.DATATYPE_FLOAT32, labels=hdr_input.labels)
    else:
        ft_output.putHeader(hdr_input.nChannels, hdr_input.fSample/downsample, FieldTrip.DATATYPE_FLOAT32, labels=hdr_input.labels)

    # initialize the state for the smoothing
    previous = np.zeros((1, hdr_input.nChannels))

    # initialize the state for differentiate/integrate
    differentiate_zi = np.zeros((1, hdr_input.nChannels))
    integrate_zi     = np.zeros((1, hdr_input.nChannels))

    # jump to the end of the input stream
    if hdr_input.nSamples<window:
        begsample = 0
        endsample = window-1
    else:
        begsample = hdr_input.nSamples-window
        endsample = hdr_input.nSamples-1


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input, ft_output
    global timeout, hdr_input, start, window, downsample, differentiate, integrate, rectify, smoothing, reference, default_scale, scale_lowpass, scale_highpass, scale_notchfilter, offset_lowpass, offset_highpass, offset_notchfilter, scale_filterorder, scale_notchquality, offset_filterorder, offset_notchquality, previous, differentiate_zi, integrate_zi, begsample, endsample
    global dat_input, dat_output, highpassfilter, lowpassfilter, filterorder, change, b, a, zi, notchfilter, notchquality, nb, na, nzi, window_new, t

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

    # determine the start of the actual processing
    start = time.time()

    dat_input  = ft_input.getData([begsample, endsample]).astype(np.float32)
    dat_output = dat_input

    monitor.trace("------------------------------------------------------------")
    monitor.trace("read        ", window, "samples in", (time.time()-start)*1000, "ms")

    # Online bandpass filtering
    highpassfilter = patch.getfloat('processing', 'highpassfilter', default=None)
    if highpassfilter != None:
        highpassfilter = EEGsynth.rescale(highpassfilter, slope=scale_highpass, offset=offset_highpass)
    lowpassfilter = patch.getfloat('processing', 'lowpassfilter', default=None)
    if lowpassfilter != None:
        lowpassfilter = EEGsynth.rescale(lowpassfilter, slope=scale_lowpass, offset=offset_lowpass)
    filterorder = patch.getfloat('processing', 'filterorder', default=int(2*hdr_input.fSample))
    if filterorder != None:
        filterorder = EEGsynth.rescale(filterorder, slope=scale_filterorder, offset=offset_filterorder)

    change = False
    change = monitor.update('highpassfilter',  highpassfilter) or change
    change = monitor.update('lowpassfilter',   lowpassfilter)  or change
    change = monitor.update('filterorder',     filterorder)    or change
    if change:
        # update the filter parameters
        filterorder = int(filterorder)                     # ensure it is an integer
        filterorder = filterorder + (filterorder%2 ==0)    # ensure it is odd
        b, a, zi = EEGsynth.initialize_online_filter(hdr_input.fSample, highpassfilter, lowpassfilter, filterorder, dat_output, axis=0)

    if not(highpassfilter is None) or not(lowpassfilter is None):
        # apply the filter to the data
        dat_output, zi = EEGsynth.online_filter(b, a, dat_output, axis=0, zi=zi)
        monitor.debug("filtered    ", window, "samples in", (time.time()-start)*1000, "ms")

    # Online notch filtering
    notchfilter = patch.getfloat('processing', 'notchfilter', default=None)
    if notchfilter != None:
        notchfilter = EEGsynth.rescale(notchfilter, slope=scale_notchfilter, offset=offset_notchfilter)
    notchquality = patch.getfloat('processing', 'notchquality', default=25)
    if notchquality != None:
        notchquality = EEGsynth.rescale(notchquality, slope=scale_notchquality, offset=offset_notchquality)

    change = False
    change = monitor.update('notchfilter',  notchfilter)  or change
    change = monitor.update('notchquality', notchquality) or change
    if change:
        # update the filter parameters
        nb, na, nzi = EEGsynth.initialize_online_notchfilter(hdr_input.fSample, notchfilter, notchquality, dat_output, axis=0)

    if not(notchfilter is None):
        # apply the filter to the data
        dat_output, nzi = EEGsynth.online_filter(nb, na, dat_output, axis=0, zi=nzi)
        monitor.debug("notched     ", window, "samples in", (time.time()-start)*1000, "ms")

    # Differentiate
    if differentiate:
        dat_output, d_zi = EEGsynth.online_filter([1, -1], 1, dat_output, axis=0, zi=differentiate_zi)

    # Integrate
    if integrate:
        dat_output, i_zi = EEGsynth.online_filter(1, [1, -1], dat_output, axis=0, zi=integrate_zi)

    # Rectifying
    if rectify:
        dat_output = np.absolute(dat_output)

    # Smoothing
    if not(smoothing is None):
        for t in range(window):
            dat_output[t, :] = smoothing * dat_output[t, :] + (1.-smoothing)*previous
            previous = copy(dat_output[t, :])
        monitor.debug("smoothed    ", window_new, "samples in", (time.time()-start)*1000, "ms")

    # Downsampling
    if not(downsample is None):
        # do not apply an anti aliassing filter, the data segment is probably too short for that
        dat_output = decimate(dat_output, downsample, n=0, ftype='iir', axis=0, zero_phase=True)
        window_new = int(window / downsample)
        monitor.debug("downsampled ", window, "samples in", (time.time()-start)*1000, "ms")
    else:
        window_new = window

    # Re-referencing
    if reference == 'median':
        dat_output -= repmat(np.nanmedian(dat_output, axis=1), dat_output.shape[1], 1).T
        monitor.debug("rereferenced (median)", window_new, "samples in", (time.time()-start)*1000, "ms")
    elif reference == 'average':
        dat_output -= repmat(np.nanmean(dat_output, axis=1), dat_output.shape[1], 1).T
        monitor.debug("rereferenced (average)", window_new, "samples in", (time.time()-start)*1000, "ms")

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32))

    monitor.info("preprocessed " + str(window_new) + " samples in " + str((time.time()-start)*1000) + " ms")
    monitor.trace("wrote       " + str(window_new) + " samples in " + str((time.time()-start)*1000) + " ms")

    # increment the counters for the next loop
    begsample += window
    endsample += window


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, ft_input, ft_output

    ft_input.disconnect()
    monitor.success('Disconnected from input FieldTrip buffer')
    ft_output.disconnect()
    monitor.success('Disconnected from output FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
