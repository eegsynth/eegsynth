#!/usr/bin/env python

# This module records data from a FieldTrip buffer to an EDF or WAV file
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
import struct

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

MININT16 = -0xffff/2 - 1
MAXINT16 =  0xffff/2 - 1
MININT32 = -0xffffffff/2 - 1
MAXINT32 =  0xffffffff/2 - 1

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
timeout     = patch.getfloat('fieldtrip', 'timeout', default=30)
filename    = patch.getstring('recording', 'file')
fileformat  = patch.getstring('recording', 'format')

if fileformat is None:
    # determine the file format from the file name
    name, ext = os.path.splitext(filename)
    fileformat = ext[1:]

try:
    ft_host = patch.getstring('fieldtrip', 'hostname')
    ft_port = patch.getint('fieldtrip', 'port')
    monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ft_host, ft_port)
    monitor.success('Connected to FieldTrip buffer')
except:
    raise RuntimeError("cannot connect to FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    monitor.info('Waiting for data to arrive...')
    if (time.time() - start) > timeout:
        raise RuntimeError("timeout while waiting for data")
    time.sleep(0.1)
    hdr_input = ft_input.getHeader()

monitor.info('Data arrived')
monitor.debug(hdr_input)
monitor.debug(hdr_input.labels)

recording = False

while True:
    monitor.loop()

    hdr_input = ft_input.getHeader()

    if recording and hdr_input is None:
        monitor.info("Header is empty - closing " + fname)
        f.close()
        recording = False
        continue

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
        # the blocksize depends on the sampling rate, which may have changed
        blocksize = int(patch.getfloat('recording', 'blocksize') * hdr_input.fSample)
        synchronize = int(patch.getfloat('recording', 'synchronize') * hdr_input.fSample)
        assert (synchronize % blocksize) == 0, "synchronize should be multiple of blocksize"

        # these are required for mapping floating point values onto 16 bit integers
        physical_min = patch.getfloat('recording', 'physical_min')
        physical_max = patch.getfloat('recording', 'physical_max')

        # write the header to file
        monitor.info("Opening " + fname)
        if fileformat == 'edf':
            # construct the header
            meas_info = {}
            chan_info = {}
            meas_info['record_length'] = blocksize / hdr_input.fSample
            meas_info['nchan'] = hdr_input.nChannels
            now = datetime.datetime.now()
            meas_info['year'] = now.year
            meas_info['month'] = now.month
            meas_info['day'] = now.day
            meas_info['hour'] = now.hour
            meas_info['minute'] = now.minute
            meas_info['second'] = now.second
            chan_info['physical_min'] = hdr_input.nChannels * [physical_min]
            chan_info['physical_max'] = hdr_input.nChannels * [physical_max]
            chan_info['digital_min'] = hdr_input.nChannels * [MININT16]
            chan_info['digital_max'] = hdr_input.nChannels * [MAXINT16]
            chan_info['ch_names'] = hdr_input.labels
            chan_info['n_samps'] = hdr_input.nChannels * [blocksize]
            monitor.info(chan_info)
            f = EDF.EDFWriter(fname)
            f.writeHeader((meas_info, chan_info))
        elif fileformat == 'wav':
            f = wave.open(fname, 'w')
            f.setnchannels(hdr_input.nChannels)
            f.setnframes(0)
            f.setsampwidth(4)  # 1, 2 or 4
            f.setframerate(hdr_input.fSample)
        else:
            raise NotImplementedError('unsupported file format')

        # determine the starting point for recording
        if hdr_input.nSamples<blocksize:
            begsample = 0
            endsample = blocksize - 1
        else:
            begsample = hdr_input.nSamples - blocksize
            endsample = hdr_input.nSamples - 1
        # remember the sample from the data stream at which the recording started
        startsample = begsample

    if recording and hdr_input.nSamples < begsample - 1:
        monitor.info("Header was reset - closing " + fname)
        f.close()
        recording = False
        continue

    if recording and endsample > hdr_input.nSamples - 1:
        # the data is not yet available
        monitor.debug("Waiting for data", endsample, hdr_input.nSamples)
        time.sleep((endsample - hdr_input.nSamples) / hdr_input.fSample)
        continue

    if recording:
        # the data is available, send a synchronization trigger prior to reading the data
        if ((endsample - startsample + 1) % synchronize) == 0:
            key = "{}.synchronize".format(patch.getstring('prefix', 'synchronize'))
            patch.setvalue(key, endsample - startsample + 1)
        dat = ft_input.getData([begsample, endsample]).astype(np.float64)
        monitor.info("Writing sample " + str(begsample) + " to " + str(endsample) " as " + str(np.shape(dat)))
        if fileformat == 'edf':
            # the scaling is done in the EDF writer
            f.writeBlock(np.transpose(dat))
        elif fileformat == 'wav':
            for sample in range(len(dat)):
                x = dat[sample, :]
                # scale the floating point values between -1 and 1
                y = x / ((physical_max - physical_min) / 2)
                # scale the floating point values between MININT32 and MAXINT32
                y = y * ((float(MAXINT32) - float(MININT32)) / 2)
                # convert them to packed binary data
                z = [int(item) for item in y]
                f.writeframesraw(wave.struct.pack('i'*len(z), *z))
        begsample += blocksize
        endsample += blocksize
