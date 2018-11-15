#!/usr/bin/env python

# Cogito processes data for the COGITO project by Daniela de Paulis
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
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

from copy import copy
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import pandas as pd
import sys
import time
import redis

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
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('input_fieldtrip','timeout')

try:
    ftc_host = patch.getstring('input_fieldtrip', 'hostname')
    ftc_port = patch.getint('input_fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

try:
    ftc_host = patch.getstring('output_fieldtrip', 'hostname')
    ftc_port = patch.getint('output_fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
    exit()

# get the input and output options
input_number, input_channel = map(list, zip(*config.items('input_channel')))
output_number, output_channel = map(list, zip(*config.items('output_channel')))

# convert to integer and make the indices zero-offset
input_number = [int(number)-1 for number in input_number]
output_number = [int(number)-1 for number in output_number]

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time()-start)>timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"
if debug > 1:
    print hdr_input
    print hdr_input.labels

# ensure that all input channels have a label
nInputs = hdr_input.nChannels
if len(hdr_input.labels) == 0:
    for i in range(nInputs):
        hdr_input.labels.append('{}'.format(i+1))

# update the labels with the ones specified in the ini file
for number, channel in zip(input_number, input_channel):
    if number < nInputs:
        hdr_input.labels[number] = channel

# update the input channel specification
input_number = range(nInputs)
input_channel = hdr_input.labels

# ensure that all output channels have a label
nOutputs = max(output_number)+1
tmp = ['{}'.format(i+1) for i in range(nOutputs)]
for number, channel in zip(output_number, output_channel):
    tmp[number] = channel

# update the output channel specification
output_number = range(nOutputs)
output_channel = tmp

if debug > 0:
    print '===== input channels ====='
    for number, channel in zip(input_number, input_channel):
        print number, '=', channel
    print '===== output channels ====='
    for number, channel in zip(output_number, output_channel):
        print number, '=', channel

sample_rate         = patch.getfloat('cogito', 'sample_rate')
window              = patch.getfloat('cogito', 'window')
f_min               = patch.getfloat('cogito', 'f_min')
f_max               = patch.getfloat('cogito', 'f_max')
f_offset            = patch.getfloat('cogito', 'f_offset')
scaling             = patch.getfloat('cogito', 'scaling')
polyorder           = patch.getint('cogito', 'polyorder',None)
profileMin          = patch.getfloat('cogito', 'profileMin')
profileMax          = patch.getfloat('cogito', 'profileMax')
profileCorrection   = np.loadtxt('Dwingeloo-Transmitter-Profile.txt')
profileCorrection   = (1. - profileCorrection)*(profileMax-profileMin) + profileMin
window              = int(round(window*hdr_input.fSample))

# FIXME these are in Hz, but should be mapped to frequency bins
f_min = int(f_min)
f_max = int(f_max)

ft_output.putHeader(nOutputs, sample_rate, hdr_input.dataType, labels=output_channel)

# Reading EEG layout
layout = pd.read_csv("gtec_layout.csv", index_col=0)
definition = 10
val = layout.loc[:, ['x', 'y', 'z']].values
val = (val - val.min())/(val.max()-val.min())*definition
positions = np.round(val).astype(int)

if debug > 1:
    print "nsample", hdr_input.nSamples
    print "nchan", hdr_input.nChannels
    print "window", window

# jump to the end of the stream
if hdr_input.nSamples-1<window:
    begsample = 0
    endsample = window-1
else:
    begsample = hdr_input.nSamples-window
    endsample = hdr_input.nSamples-1

print "STARTING COGITO STREAM"
while True:
    start_time = time.time()

    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if (hdr_input.nSamples-1)<(endsample-window):
            print "Error: buffer reset detected"
            raise SystemExit
        if (time.time()-start_time)>timeout:
            print "Error: timeout while waiting for data"
            raise SystemExit

    dat_input = ft_input.getData([begsample, endsample])

    if debug > 1:
        print 'time waiting for data: ' + str((time.time() - start_time) * 1000)

    # determine the start of the actual processing
    loop_time = time.time()

    # t = np.arange(sample_rate)
    # f = 440
    # signal = np.sin(t*f/sample_rate)*256
    # signal = np.zeros([sample_rate, 1])

    # Add offset to avoid LP filter on sound card
    tmp = [np.zeros(int(f_offset))]

    for ch in range(nInputs):
        chan_time = time.time()

        original = copy(dat_input[:, ch])

        # fit and subtract a polynomial
        t = np.arange(0, len(original))
        if not(polyorder == None):
            p = np.polynomial.polynomial.polyfit(t, original, polyorder)
            original = original - np.polynomial.polynomial.polyval(t, p)

        # One
        channel = [np.ones(1)*scaling/sample_rate]

        # Spectrum
        fourier = np.fft.rfft(original, int(sample_rate))[f_min:f_max]
        channel.append(fourier)

        # Positions
        mask = np.zeros(30)
        mask[(positions[ch][0]-1):positions[ch][0]] = scaling/int(sample_rate)
        mask[(10+positions[ch][1]-1):(10+positions[ch][1])] = scaling/int(sample_rate)
        mask[(20+positions[ch][2]-1):(20+positions[ch][2])] = scaling/int(sample_rate)
        channel.append(mask)

        # Sum of all the parts
        convert = np.concatenate(channel) * profileCorrection[ch]
        tmp.append(convert)

        if debug > 1:
            print 'time to process single channel: ' + str((time.time() - chan_time) * 1000)

    signal_time = time.time()
    signal = np.fft.irfft(np.concatenate(tmp), int(sample_rate))
    dat_output = np.atleast_2d(signal).T.astype(np.float32)

    if debug > 1:
        print 'time to inverse FFT: ' + str((time.time() - signal_time) * 1000)

    write_time = time.time()

    # write the data to the output buffer
    ft_output.putData(dat_output)

    if debug > 1:
        print 'time to write data to buffer: ' + str((time.time() - write_time) * 1000)

    # increment the counters for the next loop
    begsample += window
    endsample += window

    if debug > 0:
	    print "processed", window, "samples in", (time.time()-loop_time)*1000, "ms"
