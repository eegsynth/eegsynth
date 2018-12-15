#!/usr/bin/env python

# Outputaudio reads data from a FieldTrip buffer and writes it to an audio device
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2018 EEGsynth project
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

import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time
import pyaudio
import threading

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
timeout = patch.getfloat('fieldtrip', 'timeout', 30)

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time() - start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"
if debug > 1:
    print hdr_input
    print hdr_input.labels

device = patch.getint('audio', 'device')
window = patch.getfloat('audio', 'window', default=1)   # in seconds
window = int(window * hdr_input.fSample)                # in samples
nchans = hdr_input.nChannels                            # for the input and output
rate   = int(hdr_input.fSample)                         # for the input and output

# these are for multiplying/attenuating the signal
scaling = patch.getfloat('audio', 'scaling')
scaling_method = patch.getstring('audio', 'scaling_method')
scale_scaling  = patch.getfloat('scale', 'scaling', default=1)
offset_scaling = patch.getfloat('offset', 'scaling', default=0)

# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print key, "=", val
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}

if nchans > hdr_input.nChannels:
    print "Error: not enough channels available for output"
    raise SystemExit

if debug > 0:
    print "audio nchans", nchans
    print "audio rate", rate

p = pyaudio.PyAudio()

print '------------------------------------------------------------------'
info = p.get_host_api_info_by_index(0)
print info
print '------------------------------------------------------------------'
for i in range(info.get('deviceCount')):
    if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
        print "Input  Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
    if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
        print "Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
print '------------------------------------------------------------------'
devinfo = p.get_device_info_by_index(device)
print "Selected device is", devinfo['name']
print devinfo
print '------------------------------------------------------------------'

# this is to prevent concurrency problems
lock = threading.Lock()

stack = []
firstsample = 0
stretch = 1.

inputrate = rate
outputrate = rate

lrate = 0.1
inputblock = 0
outputblock = 0

previnput = time.time()
prevoutput = time.time()

def callback(in_data, frame_count, time_info, status):
    global stack, window, firstsample, stretch, inputrate, outputrate, outputblock, prevoutput

    now = time.time()
    duration = now - prevoutput
    prevoutput = now
    if outputblock > 5:
        old = outputrate
        new = frame_count / duration
        if old/new > 0.1 or old/new < 10:
            inputrate = (1 - lrate) * old + lrate * new

    # estimate the required stretch between input and output rate
    old = stretch
    new = inputrate / outputrate
    stretch = (1 - lrate) * old + lrate * new

    # linearly interpolate the selection of samples, i.e. stretch or compress the time axis when needed
    begsample = firstsample
    endsample = round(firstsample + stretch * frame_count)
    selection = np.linspace(begsample, endsample, frame_count).astype(np.int32)

    # remember where to continue the next time
    firstsample = (endsample + 1) % window

    with lock:
        lenstack = len(stack)
        if endsample > (window - 1):
            # the selection passes the boundary, concatenate the first two blocks
            dat = np.append(stack[0], stack[1], axis=0)
        else:
            # the selection can be made in the first block
            dat = stack[0]
    # select the samples that will be written to the audio card
    dat = dat[selection]

    if debug > 1:
        print "inputrate", int(inputrate)
        print "outputrate", int(outputrate)
        print "stretch", stretch
        print "len(stack)", lenstack

    if endsample > window:
        # it is time to remove data from the stack, keep exactly two blocks
        indx = max(0, lenstack - 2)
        with lock:
            stack = stack[indx:]

    buf = np.getbuffer(dat)
    outputblock += 1

    return buf, pyaudio.paContinue


stream = p.open(format=pyaudio.paFloat32,
                channels=nchans,
                rate=rate,
                output=True,
                output_device_index=device,
                stream_callback=callback)

# it should not start playing immediately
stream.stop_stream()

# jump to the end of the input stream
if hdr_input.nSamples - 1 < window:
    begsample = 0
    endsample = window - 1
else:
    begsample = hdr_input.nSamples - window
    endsample = hdr_input.nSamples - 1

print "STARTING STREAM"

try:
    while True:

        # measure the time that it takes
        start = time.time()

        while endsample > hdr_input.nSamples - 1:
            # wait until there is enough data
            time.sleep(patch.getfloat('general', 'delay'))
            hdr_input = ft_input.getHeader()
            if (hdr_input.nSamples - 1) < (endsample - window):
                print "Error: buffer reset detected"
                raise SystemExit
            if (time.time() - start) > timeout:
                print "Error: timeout while waiting for data"
                raise SystemExit

        dat = ft_input.getData([begsample, endsample])

        # multiply the data with the scaling factor
        scaling = patch.getfloat('audio', 'scaling', default=1)
        scaling = EEGsynth.rescale(scaling, slope=scale_scaling, offset=offset_scaling)
        show_change("scaling", scaling)
        if scaling_method == 'multiply':
            dat = dat * scaling
        elif scaling_method == 'divide':
            dat = dat / scaling

        with lock:
            stack.append(dat)

        now = time.time()
        duration = now - previnput
        previnput = now
        if inputblock > 3:
            old = inputrate
            new = window / duration
            if old/new > 0.1 or old/new < 10:
                inputrate = (1 - lrate) * old + lrate * new

        if debug > 0:
            print "read", endsample-begsample+1, "samples from", begsample, "to", endsample, "in", duration

        if len(stack) > 2:
            # there is enough data to start the output stream
            stream.start_stream()

        begsample += window
        endsample += window
        inputblock += 1

except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
