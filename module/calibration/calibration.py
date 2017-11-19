#!/usr/bin/env python

# Postprocessing performs basic algorithms on redis data
#
# Postprocessing is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

prefix      = config.get('output','prefix')
inputlist   = config.get('input','channels').split(",")
stepsize    = config.getfloat('calibration','stepsize')   # in seconds
numchannel  = len(inputlist)

# this will contain the initial and calibrated values
value = np.empty((numchannel))
value[:] = np.NAN

while True:
    # determine the start of the actual processing
    start = time.time()

    # update with current data
    for chanindx,chanstr in zip(range(numchannel), inputlist):
        try:
            chanval = EEGsynth.getfloat('input', chanstr, config, r)
        except:
            # the channel is not configured in the ini file, skip it
            continue

        if chanval==None:
            # the value is not present in redis, skip it
            continue

        if EEGsynth.getint('compressor_expander', 'enable', config, r):
            # the compressor applies to all channels and must exist as float or redis key
            lo = EEGsynth.getfloat('compressor_expander', 'lo', config, r)
            hi = EEGsynth.getfloat('compressor_expander', 'hi', config, r)
            if lo is None or hi is None:
                if debug>1:
                    print "cannot apply compressor/expander"
            else:
                # apply the compressor/expander
                chanval = EEGsynth.compress(chanval, lo, hi)

        # the scale option is channel specific
        scale = EEGsynth.getfloat('scale', chanstr, config, r, default=1)
        # the offset option is channel specific
        offset = EEGsynth.getfloat('offset', chanstr, config, r, default=0)
        # apply the scale and offset
        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)

        value[chanindx] = chanval

    for chanindx,chanstr in zip(range(numchannel), inputlist):
        for channel in range(numchannel):
            key = prefix +  "." + chanstr
            val = value[chanindx]
            r.set(key, val)

    elapsed = time.time()-start
    naptime = stepsize - elapsed
    if naptime>0:
        # this approximates the desired update speed
        time.sleep(naptime)
