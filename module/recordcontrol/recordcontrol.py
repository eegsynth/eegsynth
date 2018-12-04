#!/usr/bin/env python

# This module records Redis data to an EDF or WAV file
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project, http://www.eegsynth.org
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
import datetime
import numpy as np
import os
import redis
import sys
import time
import wave

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
import EDF

MININT16 = -np.power(2, 15)
MAXINT16 = np.power(2, 15) - 1
MININT32 = -np.power(2, 31)
MAXINT32 = np.power(2, 31) - 1

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder,
                                                            os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
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

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# this determines frequency at which the control values are sampled
delay = patch.getfloat('general', 'delay')

try:
    fileformat = patch.getstring('recording', 'format')
except:
    fname = patch.getstring('recording', 'file')
    name, ext = os.path.splitext(fname)
    fileformat = ext[1:]

filenumber = 0
recording = False
adjust = 1

while True:
    # measure the time to correct for the slip
    now = time.time()

    if recording and not patch.getint('recording', 'record'):
        if debug > 0:
            print "Recording disabled - closing", fname
        f.close()
        recording = False
        continue

    if not recording and not patch.getint('recording', 'record'):
        if debug > 0:
            print "Recording is not enabled"
        time.sleep(1)

    if not recording and patch.getint('recording', 'record'):
        recording = True
        # open a new file
        fname = patch.getstring('recording', 'file')
        name, ext = os.path.splitext(fname)
        if len(ext) == 0:
            ext = '.' + fileformat
        fname = name + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext
        # the blocksize is always 1
        blocksize = 1
        synchronize = int(patch.getfloat('recording', 'synchronize') / delay )
        assert (synchronize % blocksize) == 0, "synchronize should be multiple of blocksize"

        # get the details from Redis
        channels = sorted(r.keys('*'))
        channelz = sorted(r.keys('*'))
        nchans = len(channels)
        # this is to keep track of the number of samples written so far
        sample = 0

        # search-and-replace to reduce the length of the channel labels
        for replace in config.items('replace'):
            print replace
            for i in range(len(channelz)):
                channelz[i] = channelz[i].replace(replace[0], replace[1])
        for s, z in zip(channels, channelz):
            print "Writing control value", s, "as channel", z

        # these are required for mapping floating point values onto 16 bit integers
        physical_min = patch.getfloat('recording', 'physical_min')
        physical_max = patch.getfloat('recording', 'physical_max')

        # write the header to file
        if debug > 0:
            print "Opening", fname
        if fileformat == 'edf':
            # construct the header
            meas_info = {}
            chan_info = {}
            meas_info['record_length'] = delay
            meas_info['nchan'] = nchans
            recstart = datetime.datetime.now()
            meas_info['year'] = recstart.year
            meas_info['month'] = recstart.month
            meas_info['day'] = recstart.day
            meas_info['hour'] = recstart.hour
            meas_info['minute'] = recstart.minute
            meas_info['second'] = recstart.second
            chan_info['physical_min'] = nchans * [physical_min]
            chan_info['physical_max'] = nchans * [physical_max]
            chan_info['digital_min'] = nchans * [MININT16]
            chan_info['digital_max'] = nchans * [MAXINT16]
            chan_info['ch_names'] = channelz
            chan_info['n_samps'] = nchans * [1]
            f = EDF.EDFWriter(fname)
            f.writeHeader((meas_info, chan_info))
        elif fileformat == 'wav':
            f = wave.open(fname, 'w')
            f.setnchannels(nchans)
            f.setnframes(0)
            f.setsampwidth(4)  # 1, 2 or 4
            f.setframerate(1. / delay)
        else:
            raise NotImplementedError('unsupported file format')

    if recording:
        D = []
        for chan in channels:
            xval = r.get(chan)
            try:
                xval = float(xval)
            except ValueError:
                xval = 0.
            xval = EEGsynth.limit(xval, physical_min, physical_max)
            D.append([xval])
        sample += 1

        if (sample % synchronize) == 0:
            patch.setvalue("recordcontrol.synchronize", sample)

        if debug > 1:
            print "Writing", D
        elif debug > 0:
            print "Writing sample", sample, "as", np.shape(D)

        if fileformat == 'edf':
            f.writeBlock(D)
        elif fileformat == 'wav':
            D = np.asarray(D)
            for x in D:
                # scale the floating point values between -1 and 1
                y = x / ((physical_max - physical_min) / 2. )
                # scale the floating point values between MININT32 and MAXINT32
                y = y * ((float(MAXINT32) - float(MININT32)) / 2.)
                # convert them to packed binary data
                z = "".join((wave.struct.pack('i', item) for item in y))
                f.writeframes(z)

        time.sleep(adjust * delay)

        elapsed = time.time() - now
        # adjust the relative delay for the next iteration
        # the adjustment factor should only change a little per iteration
        adjust = 0.1 * delay / elapsed + 0.9 * adjust
