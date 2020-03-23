#!/usr/bin/env python

# This module reads data from a FieldTrip buffer and writes it to an audio device
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
import signal
import threading
import pyaudio

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


def callback(in_data, frame_count, time_info, status):
    global stack, window, firstsample, stretch, inputrate, outputrate, outputblock, prevoutput, b, a, zi

    now = time.time()
    duration = now - prevoutput
    prevoutput = now
    if outputblock > 5 and duration > 0:
        old = outputrate
        new = frame_count / duration
        if old/new > 0.1 or old/new < 10:
            outputrate = (1 - lrate) * old + lrate * new

    # estimate the required stretch between input and output rate
    old = stretch
    new = outputrate / inputrate
    stretch = (1 - lrate) * old + lrate * new

    # linearly interpolate the selection of samples, i.e. stretch or compress the time axis when needed
    begsample = firstsample
    endsample = round(firstsample + frame_count / stretch)
    selection = np.linspace(begsample, endsample, frame_count).astype(np.int32)

    # remember where to continue the next time
    firstsample = (endsample + 1) % window

    with lock:
        lenstack = len(stack)
        if endsample > (window - 1) and lenstack>1:
            # the selection passes the boundary, concatenate the first two blocks
            dat = np.append(stack[0], stack[1], axis=0)
        elif lenstack>0:
            # the selection can be made in the first block
            dat = stack[0]

    # select the samples that will be written to the audio card
    try:
        dat = dat[selection]
    except:
        dat = np.zeros((frame_count,1), dtype=float)

    if endsample > window:
        # it is time to remove data from the stack
        with lock:
            stack = stack[1:]       # remove the first block

    try:
        # this is for Python 2
        buf = np.getbuffer(dat)
    except:
        # this is for Python 3
        buf = dat.tobytes()
    outputblock += 1

    return buf, pyaudio.paContinue


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
    debug  = patch.getint('general', 'debug')

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
    global timeout, hdr_input, start, device, window, lrate, scaling_method, scaling, outputrate, scale_scaling, offset_scaling, nchans, inputrate, p, info, i, devinfo, lock, stack, firstsample, stretch, inputblock, outputblock, previnput, prevoutput, stream, begsample, endsample

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
    monitor.debug("buffer nchans", hdr_input.nChannels)
    monitor.debug("buffer rate", hdr_input.fSample)

    # get the options from the configuration file
    device  = patch.getint('audio', 'device')
    window  = patch.getfloat('audio', 'window', default=1)   # in seconds
    lrate   = patch.getfloat('clock', 'learning_rate', default=0.05)

    window      = int(window * hdr_input.fSample)               # in samples
    nchans      = hdr_input.nChannels                           # both for input as for output
    inputrate   = hdr_input.fSample

    # these are for multiplying/attenuating the signal
    scaling_method = patch.getstring('audio', 'scaling_method')
    scaling        = patch.getfloat('audio', 'scaling')
    outputrate     = patch.getint('audio', 'rate', default=int(inputrate))
    scale_scaling  = patch.getfloat('scale', 'scaling', default=1)
    offset_scaling = patch.getfloat('offset', 'scaling', default=0)

    monitor.info("audio nchans = " + str(nchans))
    monitor.info("audio rate = " + str(outputrate))

    p = pyaudio.PyAudio()

    monitor.info('------------------------------------------------------------------')
    info = p.get_host_api_info_by_index(0)
    monitor.info(info)
    monitor.info('------------------------------------------------------------------')
    for i in range(info.get('deviceCount')):
        if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
            monitor.info("Input  Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get('name'))
        if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
            monitor.info("Output Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get('name'))
    monitor.info('------------------------------------------------------------------')
    devinfo = p.get_device_info_by_index(device)
    monitor.info("Selected device is " + devinfo['name'])
    monitor.info(devinfo)
    monitor.info('------------------------------------------------------------------')

    # this is to prevent concurrency problems
    lock = threading.Lock()

    stack = []
    firstsample = 0
    stretch = outputrate / inputrate

    inputblock = 0
    outputblock = 0

    previnput = time.time()
    prevoutput = time.time()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=nchans,
                    rate=outputrate,
                    output=True,
                    output_device_index=device,
                    stream_callback=callback)

    # it should not start playing immediately
    stream.stop_stream()

    signal.signal(signal.SIGINT, _stop)

    # jump to the end of the input stream
    if hdr_input.nSamples - 1 < window:
        begsample = 0
        endsample = window - 1
    else:
        begsample = hdr_input.nSamples - window
        endsample = hdr_input.nSamples - 1

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global timeout, hdr_input, start, device, window, lrate, scaling_method, scaling, outputrate, scale_scaling, offset_scaling, nchans, inputrate, p, info, i, devinfo, lock, stack, firstsample, stretch, inputblock, outputblock, previnput, prevoutput, stream, begsample, endsample
    global dat, now, old, new, duration

    monitor.loop()

    # measure the time that it takes
    start = time.time()

    # wait only shortly, update the header after waiting
    # this fails when the data streams is stalled or when the buffer resets
    hdr_input.nSamples, hdr_input.nEvents = ft_input.wait(endsample, 0, 2000*window/hdr_input.fSample)

    # wait longer when needed, poll the buffer for new data
    # this deals with the case when the data streams is stalled or when the buffer resets
    while endsample > hdr_input.nSamples - 1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if (hdr_input.nSamples - 1) < (endsample - window):
            raise RuntimeError("buffer reset detected")
        if (time.time() - start) > timeout:
            raise RuntimeError("timeout while waiting for data")

    # the output audio is float32, hence this should be as well
    dat = ft_input.getData([begsample, endsample]).astype(np.single)

    # multiply the data with the scaling factor
    scaling = patch.getfloat('audio', 'scaling', default=1)
    scaling = EEGsynth.rescale(scaling, slope=scale_scaling, offset=offset_scaling)
    monitor.update("scaling", scaling)
    if scaling_method == 'multiply':
        dat *= scaling
    elif scaling_method == 'divide':
        dat /= scaling
    elif scaling_method == 'db':
        dat *= np.power(10, scaling/20)

    with lock:
        stack.append(dat)

    if len(stack) > 2:
        # there is enough data to start the output stream
        stream.start_stream()

    now = time.time()
    duration = now - previnput
    previnput = now
    if inputblock > 3 and duration > 0:
        old = inputrate
        new = window / duration
        if old/new > 0.1 or old/new < 10:
            inputrate = (1 - lrate) * old + lrate * new

    monitor.info("read " + str(endsample-begsample+1) + " samples from " + str(begsample) + " to " + str(endsample) + " in " + str(duration))

    monitor.update("inputrate", int(inputrate))
    monitor.update("outputrate", int(outputrate))
    monitor.update("stretch", stretch)
    monitor.update("len(stack)", len(stack))

    if np.min(dat)<-1 or np.max(dat)>1:
        monitor.warning('WARNING: signal exceeds [-1,+1] range, the audio will clip')

    begsample += window
    endsample += window
    inputblock += 1

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
    global stream, p

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
