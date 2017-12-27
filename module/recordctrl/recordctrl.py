#!/usr/bin/env python

# Recordctrl records redis data to edf file
#
# Recordctrl is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import datetime
import numpy as np
import os
import redis
import sys
import time
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
import EDF

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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

filenumber  = 0
recording   = False
delay       = patch.getfloat('general','delay')
adjust      = 1

while True:
    # measure the time to correct for the slip
    now = time.time()

    if recording and not patch.getint('recording', 'record'):
        if debug>0:
            print "Recording disabled - closing", fname
        f.close()
        recording = False
        continue

    if not recording and not patch.getint('recording', 'record'):
        if debug>0:
            print "Recording is not enabled"
        time.sleep(1)

    if not recording and patch.getint('recording', 'record'):
        recording = True
        # open a new file
        fname = patch.getstring('recording', 'file')
        name, ext = os.path.splitext(fname)
        fname = name + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext
        # get the details from REDIS
        channels = sorted(r.keys('*'))
        channelz = sorted(r.keys('*'))
        nchans = len(channels)

        # search-and-replace to reduce the length of the channel labels
        for replace in config.items('replace'):
            print replace
            for i in range(len(channelz)):
                channelz[i] = channelz[i].replace(replace[0], replace[1])
        for s,z in zip(channels, channelz):
            print "Writing control value", s, "as channel", z

        # construct the header
        meas_info = {}
        chan_info = {}
        meas_info['record_length']  = delay
        meas_info['nchan']          = nchans
        recstart = datetime.datetime.now()
        meas_info['year']           = recstart.year
        meas_info['month']          = recstart.month
        meas_info['day']            = recstart.day
        meas_info['hour']           = recstart.hour
        meas_info['minute']         = recstart.minute
        meas_info['second']         = recstart.second
        chan_info['physical_min']   = nchans * [-1024.] # FIXME
        chan_info['physical_max']   = nchans * [ 1024.]
        chan_info['digital_min']    = nchans * [-32768]
        chan_info['digital_max']    = nchans * [ 32768]
        chan_info['ch_names']       = channelz
        chan_info['n_samps']        = nchans * [1]
        # write the header to file
        if debug>0:
            print "Opening", fname
        f = EDF.EDFWriter(fname)
        f.writeHeader((meas_info, chan_info))

    if recording:
        D = []
        for chan in channels:
            D.append([float(r.get(chan))])
        if debug>1:
            print "Writing", D
        f.writeBlock(D)
        time.sleep(adjust * delay)

        elapsed = time.time() - now
        # adjust the relative delay for the next iteration
        # the adjustment factor should only change a little per iteration
        adjust = 0.1 * delay/elapsed + 0.9 * adjust
