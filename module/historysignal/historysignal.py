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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth
import FieldTrip

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale

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
timeout = patch.getfloat('fieldtrip', 'timeout')

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
    if (time.time()-start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug > 1:
    print "input nsample", hdr_input.nSamples
    print "input nchan", hdr_input.nChannels

inputlist   = patch.getint('input', 'channels', multiple=True)
prefix      = patch.getstring('output', 'prefix')
enable      = patch.getint('history', 'enable', default=1)
stepsize    = patch.getfloat('history', 'stepsize')                 # in seconds
window      = patch.getfloat('history', 'window')                   # in seconds
stepsize    = int(round(hdr_input.fSample*stepsize))                # in samples
numhistory  = int(round(hdr_input.fSample*window))                  # in samples
numchannel  = len(inputlist)

# jump to the end of the stream
if hdr_input.nSamples-1<stepsize:
    begsample = 0
    endsample = stepsize-1
else:
    begsample = hdr_input.nSamples-stepsize
    endsample = hdr_input.nSamples-1

# see https://en.wikipedia.org/wiki/Median_absolute_deviation
def mad(arr, axis=None):
    if axis==1:
        val = np.apply_along_axis(mad, 1, arr)
    else:
        val = np.nanmedian(np.abs(arr - np.nanmedian(arr)))
    return val

# this will contain the full list of historic values
history = np.empty((numhistory, numchannel)) * np.NAN

# this will contain the statistics of the historic values
historic = {}

while True:
    # determine the start of the actual processing
    start = time.time()

    # update the enable status
    prev_enable = enable
    enable = patch.getint('history', 'enable', default=1)

    if enable and prev_enable:
        if debug > 0:
            print "Updating"
    elif enable and not prev_enable:
        if debug > 0:
            print "Enabling the updating"
            # jump to the end of the stream
            hdr_input = ft_input.getHeader()
            begsample = hdr_input.nSamples-stepsize
            endsample = hdr_input.nSamples-1
    elif not enable and not prev_enable:
        if debug > 0:
            print "Not updating"
    elif not enable and prev_enable:
        if debug > 0:
            print "Disabling the updating"

    if not enable:
        time.sleep(patch.getfloat('general', 'delay'))

    else:
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

        if debug>1:
            print "reading samples", begsample, "to", endsample

        # get the input data, sample vector and time vector
        dat_input = ft_input.getData([begsample, endsample])

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

        for operation in historic.keys():
            key = prefix + "." + operation
            val = historic[operation]
            patch.setvalue(key, val, debug>1)

        begsample += stepsize
        endsample += stepsize
