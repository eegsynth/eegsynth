#!/usr/bin/env python

# Audio2ft reads data from an audio device and writes it to a FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2020 EEGsynth project
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
import numpy as np
import os
import redis
import sys
import time
import pyaudio

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
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
device      = patch.getint('audio', 'device')
rate        = patch.getint('audio', 'rate', default=44100)
blocksize   = patch.getint('audio', 'blocksize', default=1024)
nchans      = patch.getint('audio', 'nchans', default=2)

try:
    ft_host = patch.getstring('fieldtrip', 'hostname')
    ft_port = patch.getint('fieldtrip', 'port')
    monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
    ft_output = FieldTrip.Client()
    ft_output.connect(ft_host, ft_port)
    monitor.success('Connected to output FieldTrip buffer')
except:
    raise RuntimeError("cannot connect to output FieldTrip buffer")

monitor.info("rate = %g" % rate)
monitor.info("nchans = %g" % nchans)
monitor.info("blocksize = %g" % blocksize)

p = pyaudio.PyAudio()

monitor.info('------------------------------------------------------------------')
info = p.get_host_api_info_by_index(0)
monitor.info(info)
monitor.info('------------------------------------------------------------------')
for i in range(info.get('deviceCount')):
    if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
        monitor.info("Input  Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get('name'))
    if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
        monitor.info("Output Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get('name'))
monitor.info('------------------------------------------------------------------')
devinfo = p.get_device_info_by_index(device)
monitor.info("Selected device is " + devinfo['name'])
monitor.info(devinfo)
monitor.info('------------------------------------------------------------------')

stream = p.open(format=pyaudio.paInt16,
                channels=nchans,
                rate=rate,
                input=True,
                input_device_index=device,
                frames_per_buffer=blocksize)

ft_output.putHeader(nchans, float(rate), FieldTrip.DATATYPE_INT16)

startfeedback = time.time()
countfeedback = 0

while True:
    monitor.loop()

    # measure the time that it takes
    start = time.time()

    # read a block of data from the audio device
    data = stream.read(blocksize)

    # convert raw buffer to numpy array and write to output buffer
    data = np.reshape(np.frombuffer(data, dtype=np.int16), (blocksize, nchans))
    ft_output.putData(data)

    countfeedback += blocksize

    if debug > 1:
        monitor.print("streamed", blocksize, "samples in", (time.time() - start) * 1000, "ms")
    elif debug > 0 and countfeedback >= rate:
        # this gets printed approximately once per second
        monitor.print("streamed", countfeedback, "samples in", (time.time() - startfeedback) * 1000, "ms")
        startfeedback = time.time()
        countfeedback = 0

stream.stop_stream()
stream.close()
p.terminate()
