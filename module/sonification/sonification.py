#!/usr/bin/env python

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

from copy import copy
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
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

debug       = patch.getint('general', 'debug')                 # this determines how much debugging information gets printed
timeout     = patch.getfloat('input_fieldtrip', 'timeout')     # this is the timeout for the FieldTrip buffer
sample_rate = patch.getfloat('sonification', 'sample_rate')
f_offset    = patch.getfloat('sonification', 'f_offset')
f_order     = patch.getint('sonification', 'f_order', default=15)
window      = patch.getfloat('sonification', 'window')
sideband    = patch.getstring('sonification', 'sideband')

# these are for multiplying/attenuating the output signal
scaling        = patch.getfloat('sonification', 'scaling')
scaling_method = patch.getstring('sonification', 'scaling_method')
scale_scaling  = patch.getfloat('scale', 'scaling', default=1)
offset_scaling = patch.getfloat('offset', 'scaling', default=0)

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

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time()-start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"

if debug > 1:
    print "input nsample", hdr_input.nSamples
    print "input nchan", hdr_input.nChannels

# set up the output data stream
ft_output.putHeader(1, sample_rate, FieldTrip.DATATYPE_FLOAT32, ['audio'])
hdr_output = ft_output.getHeader()

if debug > 1:
    print "output nsample", hdr_output.nSamples
    print "output nchan", hdr_output.nChannels

# this is the number of samples per input and per output block
nInput = int(round(window*hdr_input.fSample))
nOutput = int(round(window*hdr_output.fSample))

# jump to the end of the stream
if hdr_input.nSamples-1<nInput:
    begsample = 0
    endsample = nInput-1
else:
    begsample = hdr_input.nSamples-nInput
    endsample = hdr_input.nSamples-1

dat_output = np.zeros(nOutput)

b = [None] * hdr_input.nChannels
a = [None] * hdr_input.nChannels
zi = [None] * hdr_input.nChannels
for i in range(0, hdr_input.nChannels):
    if sideband == 'lsb':
        b[i], a[i], zi[i] = EEGsynth.initialize_online_filter(hdr_output.fSample, None, (i + 1) * f_offset, f_order, dat_output)
    elif sideband == 'usb':
        b[i], a[i], zi[i] = EEGsynth.initialize_online_filter(hdr_output.fSample, (i + 1) * f_offset, None, f_order, dat_output)
    else:
        b[i], a[i], zi[i] = EEGsynth.initialize_online_filter(hdr_output.fSample, None, None, f_order, dat_output)

print "STARTING STREAM"

while True:

    start = time.time()
    while endsample > hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if hdr_input.nSamples < begsample:
            print "Error: buffer reset detected"
            raise SystemExit
        if (time.time()-start) > timeout:
            print "Error: timeout while waiting for data"
            raise SystemExit

    # get the input data, sample vector and time vector
    dat_input = ft_input.getData([begsample, endsample])
    smp_input = np.arange(begsample, endsample+1)
    tim_input = smp_input / hdr_input.fSample

    # construct a time vector corresponding to the output samples
    tim_output = np.linspace(tim_input[0], tim_input[-1], nOutput)
    dat_output = np.zeros(nOutput)

    for i in range(0, hdr_input.nChannels):
        # interpolate each channel onto the output sampling rate
        vec_output = np.interp(tim_output, tim_input, dat_input[:, i])
        # multiply with the modulating signal
        vec_output *= np.cos(tim_output * (i+1) * f_offset * 2 * np.pi)
        # apply the filter to remove one sideband
        vec_output, zi[i] = EEGsynth.online_filter(b[i], a[i], vec_output, zi=zi[i])
        # add it to the output
        dat_output += vec_output
    # normalize for the number of channels
    dat_output /= hdr_input.nChannels

    scaling = patch.getfloat('signal', 'scaling', default=1)
    scaling = EEGsynth.rescale(scaling, slope=scale_scaling, offset=offset_scaling)
    if scaling_method == 'multiply':
        dat_output *= scaling
    elif scaling_method == 'divide':
        dat_output /= scaling

#    dat_output = np.random.randn(dat_output.shape[0])
#    dat_output += np.cos(tim_output * ((i + 1) * f_offset - 50) * 2 * np.pi)
#    dat_output += np.cos(tim_output * ((i + 1) * f_offset + 50) * 2 * np.pi)

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32).reshape(nOutput, 1))

    # compute the desired number of output samples
    duration = time.time() - start
    desired = duration * sample_rate

    if debug>0:
        print "wrote", nInput, "->", nOutput, "samples in", duration*1000, "ms"

    # update the number of output samples for the next iteration
    if nOutput > desired:
        nOutput /= 1.002
    elif nOutput < desired:
        nOutput *= 1.002
    nOutput = int(round(nOutput))

    # shift to the next block of data
    begsample += nInput
    endsample += nInput
