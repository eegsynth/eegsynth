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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std
import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time

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
timeout     = patch.getfloat('fieldtrip', 'timeout', default=30)
inputlist   = patch.getint('input', 'channels', multiple=True)
prefix      = patch.getstring('output', 'prefix')
enable      = patch.getint('history', 'enable', default=1)
stepsize    = patch.getfloat('history', 'stepsize')                 # in seconds
window      = patch.getfloat('history', 'window')                   # in seconds

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to input FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to input FieldTrip buffer")

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

if debug > 1:
    print("input nsample", hdr_input.nSamples)
    print("input nchan", hdr_input.nChannels)

stepsize    = int(round(hdr_input.fSample*stepsize))                # in samples
numhistory  = int(round(hdr_input.fSample*window))                  # in samples
numchannel  = len(inputlist)

# this will contain the full list of historic values
history = np.empty((numhistory, numchannel)) * np.NAN

# this will contain the statistics of the historic values
historic = {}


# see https://en.wikipedia.org/wiki/Median_absolute_deviation
def mad(arr, axis=None):
    if axis==1:
        val = np.apply_along_axis(mad, 1, arr)
    else:
        val = np.nanmedian(np.abs(arr - np.nanmedian(arr)))
    return val


# jump to the end of the stream
if hdr_input.nSamples-1<stepsize:
    begsample = 0
    endsample = stepsize-1
else:
    begsample = hdr_input.nSamples-stepsize
    endsample = hdr_input.nSamples-1

while True:
    monitor.loop()
    # determine the start of the actual processing
    start = time.time()

    # update the enable status
    prev_enable = enable
    enable = patch.getint('history', 'enable', default=1)

    if enable and prev_enable:
        if debug > 0:
            print("Updating the history")
    elif enable and not prev_enable:
        if debug > 0:
            print("Enabling the updating")
            # jump to the end of the stream
            hdr_input = ft_input.getHeader()
            begsample = hdr_input.nSamples-stepsize
            endsample = hdr_input.nSamples-1
    elif not enable and not prev_enable:
        if debug > 0:
            print("Not updating the history")
    elif not enable and prev_enable:
        if debug > 0:
            print("Disabling the updating")

    if not enable:
        time.sleep(patch.getfloat('general', 'delay'))

    else:
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

        if debug>1:
            print("reading samples", begsample, "to", endsample)

        # get the input data, sample vector and time vector
        dat_input = ft_input.getData([begsample, endsample]).astype(np.double)

        # shift the history and insert the most recent data
        history = np.roll(history, stepsize, axis=0)
        chanindx = np.asarray(inputlist,np.int32)-1
        history[-stepsize:,] = dat_input[:,chanindx]

        # compute some statistics
        historic['mean']    = np.nanmean(history.flatten(), axis=0)
        historic['std']     = np.nanstd(history.flatten(), axis=0)
        historic['min']     = np.nanmin(history.flatten(), axis=0)
        historic['max']     = np.nanmax(history.flatten(), axis=0)
        historic['range']   = historic['max'] - historic['min']

        if False:
            # use some robust estimators
            historic['median']  = np.nanmedian(history.flatten(), axis=0)
            # see https://en.wikipedia.org/wiki/Median_absolute_deviation
            historic['mad']     = mad(history.flatten(), axis=0)
            # for a normal distribution the 16th and 84th percentile correspond to the mean plus-minus one standard deviation
            historic['p03']     = np.percentile(history.flatten(),  3, axis=0) # mean minus 2x standard deviation
            historic['p16']     = np.percentile(history.flatten(), 16, axis=0) # mean minus 1x standard deviation
            historic['p84']     = np.percentile(history.flatten(), 84, axis=0) # mean plus 1x standard deviation
            historic['p97']     = np.percentile(history.flatten(), 97, axis=0) # mean plus 2x standard deviation
            # see https://en.wikipedia.org/wiki/Interquartile_range
            historic['iqr']     = historic['p84'] - historic['p16']

        for operation in list(historic.keys()):
            key = prefix + "." + operation
            val = historic[operation]
            patch.setvalue(key, val, debug>1)

        begsample += stepsize
        endsample += stepsize
