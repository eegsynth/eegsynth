#!/usr/bin/env python

# This module records Redis data to an EDF or WAV file
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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
import datetime
import numpy as np
import os
import redis
import sys
import time
import wave

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
import EDF

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

MININT16 = -np.power(2., 15)
MAXINT16 =  np.power(2., 15) - 1
MININT32 = -np.power(2., 31)
MAXINT32 =  np.power(2., 31) - 1

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
delay       = patch.getfloat('general', 'delay')
filename    = patch.getstring('recording', 'file')
fileformat  = patch.getstring('recording', 'format')

if fileformat is None:
    # determine the file format from the file name
    name, ext = os.path.splitext(filename)
    fileformat = ext[1:]

filenumber = 0
recording = False
adjust = 1

while True:
    monitor.loop()

    # measure the time to correct for the slip
    start = time.time()

    if recording and not patch.getint('recording', 'record'):
        monitor.info("Recording disabled - closing " + fname)
        f.close()
        recording = False
        continue

    if not recording and not patch.getint('recording', 'record'):
        monitor.info("Recording is not enabled")
        time.sleep(1)

    if not recording and patch.getint('recording', 'record'):
        recording = True
        # open a new file
        name, ext = os.path.splitext(filename)
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
            monitor.debug(replace)
            for i in range(len(channelz)):
                channelz[i] = channelz[i].replace(replace[0], replace[1])
        for s, z in zip(channels, channelz):
            monitor.info("Writing control value " + s + " as channel " + z)

        # these are required for mapping floating point values onto 16 bit integers
        physical_min = patch.getfloat('recording', 'physical_min')
        physical_max = patch.getfloat('recording', 'physical_max')

        # write the header to file
        monitor.info("Opening " + fname)
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
            key = "{}.synchronize".format(patch.getstring('prefix', 'synchronize'))
            patch.setvalue(key, sample)

        monitor.info("Writing sample " + str(sample) +  " as " + str(np.shape(D)))

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
                f.writeframesraw(z)

        time.sleep(adjust * delay)

        elapsed = time.time() - start
        # adjust the relative delay for the next iteration
        # the adjustment factor should only change a little per iteration
        adjust = 0.1 * delay / elapsed + 0.9 * adjust
