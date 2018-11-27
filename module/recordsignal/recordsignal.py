#!/usr/bin/env python

# This module records data from a FieldTrip buffer to an EDF or WAV file
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

import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout')

try:
    fileformat = patch.getstring('recording', 'format')
except:
    fname = patch.getstring('recording', 'file')
    name, ext = os.path.splitext(fname)
    fileformat = ext[1:]

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time() - start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"
if debug > 1:
    print hdr_input
    print hdr_input.labels

recording = False

while True:
    hdr_input = ftc.getHeader()

    if recording and hdr_input is None:
        if debug > 0:
            print "Header is empty - closing", fname
        f.close()
        recording = False
        continue

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
        # the blocksize depends on the sampling rate, which may have changed
        blocksize = int(patch.getfloat('recording', 'blocksize') * hdr_input.fSample)
        synchronize = int(patch.getfloat('recording', 'synchronize') * hdr_input.fSample)
        assert (synchronize % blocksize) == 0, "synchronize should be multiple of blocksize"

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
            print chan_info
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
        if hdr_input.nSamples > blocksize:
            endsample = hdr_input.nSamples - 1
            begsample = endsample - blocksize + 1
        else:
            endsample = blocksize - 1
            begsample = endsample - blocksize + 1
        # remember the sample from the data stream at which the recording started
        startsample = begsample

    if recording and hdr_input.nSamples < begsample - 1:
        if debug > 0:
            print "Header was reset - closing", fname
        f.close()
        recording = False
        continue

    if recording and endsample > hdr_input.nSamples - 1:
        # the data is not yet available
        if debug > 2:
            print "Waiting for data", endsample, hdr_input.nSamples
        time.sleep((endsample - hdr_input.nSamples) / hdr_input.fSample)
        continue

    if recording:
        # the data is available, send a synchronization trigger prior to reading the data
        if ((endsample - startsample + 1) % synchronize) == 0:
            patch.setvalue("recordsignal.synchronize", endsample - startsample + 1)
        D = ftc.getData([begsample, endsample])
        if debug > 0:
            print "Writing sample", begsample, "to", endsample, "as", np.shape(D)
        if fileformat == 'edf':
            f.writeBlock(np.transpose(D))
        elif fileformat == 'wav':
            for sample in range(len(D)):
                x = D[sample, :]
                # scale the floating point values between -1 and 1
                y = x / ((physical_max - physical_min) / 2)
                # scale the floating point values between MININT32 and MAXINT32
                y = y * ((float(MAXINT32) - float(MININT32)) / 2)
                # convert them to packed binary data
                z = "".join((wave.struct.pack('i', item) for item in y))
                f.writeframes(z)
        begsample += blocksize
        endsample += blocksize
