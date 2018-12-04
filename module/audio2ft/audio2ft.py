#!/usr/bin/env python

# Audio2ft reads data from an audio device and writes it to a FieldTrip buffer
#
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

import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time
import pyaudio

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

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
    exit()

device      = patch.getint('audio', 'device')
rate        = patch.getint('audio', 'rate', default=44100)
blocksize   = patch.getint('audio', 'blocksize', default=1024)
nchans      = patch.getint('audio', 'nchans', default=2)

if debug > 0:
    print "rate", rate
    print "nchans", nchans
    print "blocksize", blocksize

p = pyaudio.PyAudio()

print '------------------------------------------------------------------'
info = p.get_host_api_info_by_index(0)
print info
print '------------------------------------------------------------------'
for i in range(info.get('deviceCount')):
    if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
        print "Input  Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
    if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
        print "Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
print '------------------------------------------------------------------'
devinfo = p.get_device_info_by_index(device)
print "Selected device is", devinfo['name']
print devinfo
print '------------------------------------------------------------------'

stream = p.open(format=pyaudio.paInt16,
                channels=nchans,
                rate=rate,
                input=True,
                input_device_index=device,
                frames_per_buffer=blocksize)

ft_output.putHeader(nchans, float(rate), FieldTrip.DATATYPE_INT16)

startfeedback = time.time()
countfeedback = 0

print "STARTING STREAM"
while True:

    # measure the time that it takes
    start = time.time()

    # read a block of data from the audio device
    data = stream.read(blocksize)

    # convert raw buffer to numpy array and write to output buffer
    data = np.reshape(np.frombuffer(data, dtype=np.int16), (blocksize, nchans))
    ft_output.putData(data)

    countfeedback += blocksize

    if debug > 1:
        print "streamed", blocksize, "samples in", (time.time() - start) * 1000, "ms"
    elif debug > 0 and countfeedback >= rate:
        # this gets printed approximately once per second
        print "streamed", countfeedback, "samples in", (time.time() - startfeedback) * 1000, "ms"
        startfeedback = time.time()
        countfeedback = 0

stream.stop_stream()
stream.close()
p.terminate()
