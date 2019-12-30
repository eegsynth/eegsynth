#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2019 EEGsynth project
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
import configparser
import argparse
import numpy as np
import os
import sys
import time
import redis

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
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
timeout     = patch.getfloat('input_fieldtrip', 'timeout', default=30)
sample_rate = patch.getfloat('sonification', 'sample_rate')
f_shift     = patch.getstring('sonification', 'f_shift')
f_offset    = patch.getfloat('sonification', 'f_offset')
f_order     = patch.getint('sonification', 'f_order', default=15)
window      = patch.getfloat('sonification', 'window')
sideband    = patch.getstring('sonification', 'sideband')
left        = patch.getint('sonification', 'left', multiple=True)
right       = patch.getint('sonification', 'right', multiple=True)

# these are for multiplying/attenuating the output signal
scaling        = patch.getfloat('sonification', 'scaling')
scaling_method = patch.getstring('sonification', 'scaling_method')
scale_scaling  = patch.getfloat('scale', 'scaling', default=1)
offset_scaling = patch.getfloat('offset', 'scaling', default=0)

try:
    float(config.get('processing', 'highpassfilter'))
    float(config.get('processing', 'lowpassfilter'))
    # the filter frequencies are specified as numbers
    default_scale = 1.
except:
    # the filter frequencies are specified as Redis channels
    # scale them to the Nyquist frequency
    default_scale = sample_rate/2

# these are for bandpass filtering
scale_lowpass       = patch.getfloat('scale', 'lowpassfilter', default=default_scale)
scale_highpass      = patch.getfloat('scale', 'highpassfilter', default=default_scale)
offset_lowpass      = patch.getfloat('offset', 'lowpassfilter', default=0)
offset_highpass     = patch.getfloat('offset', 'highpassfilter', default=0)
scale_filterorder   = patch.getfloat('scale', 'filterorder', default=1)
offset_filterorder  = patch.getfloat('offset', 'filterorder', default=0)

try:
    ftc_host = patch.getstring('input_fieldtrip', 'hostname')
    ftc_port = patch.getint('input_fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to input FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to input FieldTrip buffer")

try:
    ftc_host = patch.getstring('output_fieldtrip', 'hostname')
    ftc_port = patch.getint('output_fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to output FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to output FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print("Waiting for data to arrive...")
    if (time.time()-start) > timeout:
        print("Error: timeout while waiting for data")
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.1)

if debug > 0:
    print("Data arrived")

if debug > 1:
    print("input nsample", hdr_input.nSamples)
    print("input nchan", hdr_input.nChannels)

# set up the output data stream
if len(right)>0:
    # left and right, i.e. stereo
    ft_output.putHeader(2, sample_rate, FieldTrip.DATATYPE_FLOAT32, ['left', 'right'])
else:
    # only left, i.e. mono
    ft_output.putHeader(1, sample_rate, FieldTrip.DATATYPE_FLOAT32, ['mono'])
hdr_output = ft_output.getHeader()

if debug > 1:
    print("output nsample", hdr_output.nSamples)
    print("output nchan", hdr_output.nChannels)

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

# this is for a single channel
dat_output = np.zeros(nOutput)

left_f = [None] * len(left)
left_b = [None] * len(left)
left_a = [None] * len(left)
left_zi = [None] * len(left)

right_f = [None] * len(right)
right_b = [None] * len(right)
right_a = [None] * len(right)
right_zi = [None] * len(right)

for i in range(0,len(left)):
    if f_shift == 'linear':
        left_f[i] = f_offset * (i + 1)
    else:
        left_f[i] = f_offset * 2**i

    if sideband == 'usb':
        highpass = left_f[i]
        lowpass = None
    elif sideband == 'lsb':
        highpass = None
        lowpass = left_f[i]
    else:
        highpass = None
        lowpass = None
    left_b[i], left_a[i], left_zi[i] = EEGsynth.initialize_online_filter(hdr_output.fSample, highpass, lowpass, f_order, dat_output)

for i in range(0,len(right)):
    if f_shift == 'linear':
        right_f[i] = f_offset * (i + 1)
    else:
        right_f[i] = f_offset * 2**i

    if sideband == 'usb':
        highpass = right_f[i]
        lowpass = None
    elif sideband == 'lsb':
        highpass = None
        lowpass = right_f[i]
    else:
        highpass = None
        lowpass = None
    right_b[i], right_a[i], right_zi[i] = EEGsynth.initialize_online_filter(hdr_output.fSample, highpass, lowpass, f_order, dat_output)

if debug>0:
    print("left audio channels", left)
    print("left audio frequencies", left_f)
    print("right audio channels", right)
    print("right audio frequencies", right_f)

while True:
    monitor.loop()
    start = time.time()

    while endsample > hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(patch.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()
        if hdr_input.nSamples < begsample:
            print("Error: buffer reset detected")
            raise SystemExit
        if (time.time()-start) > timeout:
            print("Error: timeout while waiting for data")
            raise SystemExit

    # get the input data
    dat_input = ft_input.getData([begsample, endsample]).astype(np.double)
    dat_output = np.zeros((nOutput,hdr_output.nChannels))

    # construct a time vector for input and output
    begtime = float(begsample  ) / hdr_input.fSample
    endtime = float(endsample+1) / hdr_input.fSample
    tim_input = np.linspace(begtime, endtime, nInput, endpoint=False)
    tim_output = np.linspace(begtime, endtime, nOutput, endpoint=False)

    for chan, i in zip(left, list(range(len(left)))):
        # interpolate each channel onto the output sampling rate
        vec_output = np.interp(tim_output, tim_input, dat_input[:, chan-1])
        # multiply with the modulating signal
        vec_output *= np.cos(tim_output * left_f[i] * 2 * np.pi)
        if highpass != None or lowpass != None:
            # apply the filter to remove one sideband
            vec_output, left_zi[i] = EEGsynth.online_filter(left_b[i], left_a[i], vec_output, zi=left_zi[i])
        # add it to the left-channel output
        dat_output[:,0] += vec_output

    for chan, i in zip(right, list(range(len(right)))):
        # interpolate each channel onto the output sampling rate
        vec_output = np.interp(tim_output, tim_input, dat_input[:, chan-1])
        # multiply with the modulating signal
        vec_output *= np.cos(tim_output * right_f[i] * 2 * np.pi)
        if highpass != None or lowpass != None:
            # apply the filter to remove one sideband
            vec_output, right_zi[i] = EEGsynth.online_filter(right_b[i], right_a[i], vec_output, zi=right_zi[i])
        # add it to the right-channel output
        dat_output[:,1] += vec_output

    # Online filtering
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

    # normalize for the number of channels
    dat_output /= hdr_input.nChannels

    scaling = patch.getfloat('signal', 'scaling', default=1)
    scaling = EEGsynth.rescale(scaling, slope=scale_scaling, offset =offset_scaling)
    if scaling_method == 'multiply':
        dat_output *=  scaling
    elif scaling_method == 'divide':
        dat_output /= scaling
    elif scaling_method == 'db':
        dat_output *= np.power(10, scaling/20)

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32))

    # compute the duration and desired number of output samples
    duration = time.time() - start
    desired = duration * sample_rate

    # update the number of output samples for the next iteration
    #    if nOutput > desired:
    #        nOutput /= 1.002
    #    elif nOutput < desired:
    #        nOutput *= 1.002
    #    nOutput = int(round(nOutput))

    if debug>0:
        print("wrote", nInput, "->", nOutput, "samples in", duration*1000, "ms")

    # shift to the next block of data
    begsample += nInput
    endsample += nInput
