#!/usr/bin/env python

# Sampler plays audio samples
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
import scipy.io
from scipy.io import wavfile
import os
import redis
import sys
import time
import pyaudio
import threading

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
debug           = patch.getint('general', 'debug')
device          = patch.getint('audio', 'device')
scaling_method  = patch.getstring('audio', 'scaling_method')
scaling         = patch.getfloat('audio', 'scaling', default=1)
speed           = patch.getfloat('audio', 'scaling', default=1)
onset           = patch.getfloat('audio', 'scaling', default=0)
offset          = patch.getfloat('audio', 'scaling', default=1)
taper           = patch.getfloat('audio', 'taper', default=0)
scale_scaling   = patch.getfloat('scale', 'scaling', default=1)
scale_speed     = patch.getfloat('scale', 'speed', default=1)
scale_onset     = patch.getfloat('scale', 'onset', default=1)
scale_offset    = patch.getfloat('scale', 'offset', default=1)
scale_taper     = patch.getfloat('scale', 'taper', default=1)
offset_scaling  = patch.getfloat('offset', 'scaling', default=0)
offset_speed    = patch.getfloat('offset', 'speed', default=0)  # the default is from 0.5x to 1.5x
offset_onset    = patch.getfloat('offset', 'onset', default=0)
offset_offset   = patch.getfloat('offset', 'offset', default=0)
offset_taper    = patch.getfloat('offset', 'taper', default=0)
started         = patch.getstring('prefix', 'started', default='started')
finished        = patch.getstring('prefix', 'finished', default='finished')

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

# this is to prevent concurrency problems
lock = threading.Lock()

input_channel, input_sample = list(zip(*config.items('input')))
input_sample = [x.split(',') for x in input_sample]

# open first file to determine the format
rate, dat = wavfile.read(input_sample[0][0])

if len(dat.shape)==1:
    channels = 1
else:
    channels = dat.shape[1]

stack = np.zeros((0,channels), dtype=np.float32)

# these serve to remember the channel that triggered the sample
current_channel = None
current_value = 0

def callback(in_data, frame_count, time_info, status):
    global debug, stack, channels, prefix, current_channel, current_value

    with lock:
        begsample = 0
        endsample = min(frame_count, stack.shape[0])
        dat = stack[begsample:endsample]
        # add zero-padding if required
        pad = np.zeros((frame_count-endsample,channels), dtype=np.float32)
        dat = np.concatenate((dat,pad), axis=0)
        # remove the current samples from the stack
        stack = stack[endsample:]

    if stack.shape[0]==0 and current_channel!=None:
        # send a trigger to indicate that the sample finished playing
        patch.setvalue("%s.%s" % (finished, current_channel), current_value)
        current_channel = None
        current_value = 0

    try:
        # this is for Python 2
        buf = np.getbuffer(dat)
    except:
        # this is for Python 3
        buf = dat.tobytes()

    return buf, pyaudio.paContinue

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, sample):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.sample = sample
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        global stack, current_channel, current_value
        pubsub = r.pubsub()
        pubsub.subscribe('SAMPLER_UNBLOCK') # this message unblocks the Redis listen command
        pubsub.subscribe(self.redischannel) # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    # if value=0, the previous sample is stopped
                    # if value=N, the Nth sample is played
                    val = float(item['data'])
                    scale_data = patch.getfloat('scale', self.redischannel, default=1)
                    offset_data = patch.getfloat('offset', self.redischannel, default=0)
                    val = EEGsynth.rescale(val, slope=scale_data, offset=offset_data)
                    val = int(val)

                    if val == 0:
                        if current_channel == self.redischannel:
                            with lock:
                                stack = np.zeros((0,channels), dtype=np.float32)
                                current_channel = None
                                current_value = val

                    elif len(self.sample)>=val:
                        # update the parameters
                        scaling = patch.getfloat('audio', 'scaling', default=1)
                        scaling = EEGsynth.rescale(scaling, slope=scale_scaling, offset=offset_scaling)
                        monitor.update("scaling", scaling)

                        speed = patch.getfloat('audio', 'speed', default=1)
                        speed = EEGsynth.rescale(speed, slope=scale_speed, offset=offset_speed)
                        monitor.update("speed", speed)

                        onset = patch.getfloat('audio', 'onset', default=0)
                        onset = EEGsynth.rescale(onset, slope=scale_onset, offset=offset_onset)
                        monitor.update("onset", onset)

                        offset = patch.getfloat('audio', 'offset', default=1)
                        offset = EEGsynth.rescale(offset, slope=scale_offset, offset=offset_offset)
                        monitor.update("offset", offset)

                        taper = patch.getfloat('audio', 'taper', default=0)
                        taper = EEGsynth.rescale(taper, slope=scale_taper, offset=offset_taper)
                        monitor.update("taper", taper)

                        # read the audio file
                        filename = self.sample[val-1]
                        try:
                            rate, dat = wavfile.read(filename)
                            # ensure it is a two-dimensional array with samples*channels
                            dat = np.reshape(dat, (dat.shape[0], channels))
                            # trim to the onset/offset and adjust the speed
                            begsample = round(dat.shape[0]*onset)
                            endsample = round(dat.shape[0]*offset)
                            endsample = max(begsample, endsample)
                            count = round((endsample-begsample)/speed)
                            selection = np.linspace(begsample, endsample-1, count).astype(np.int32)
                            dat = dat[selection]
                            monitor.info("playing %s for up to %d ms" % (filename, 1000*dat.shape[0]/rate))
                        except:
                            module.warning("cannot load %s" % filename)
                            continue

                        # deal with empty files or selections
                        if dat.shape[0]==0:
                            dat = np.zeros((1, channels))

                        # scale 8, 16 and 32 bit PCM to float, with values between -1.0 and +1.0
                        if dat.dtype == np.uint8:
                            dat = (dat.astype(np.float32) - 127.) / 255.
                        elif dat.dtype == np.int16:
                            dat = dat.astype(np.float32) / 32767.
                        elif dat.dtype == np.int32:
                            dat = dat.astype(np.float32) / 2147483647.

                        # taper the rising and falling flank
                        if taper>0:
                            n = np.floor(dat.shape[0]*taper/2).astype(int)
                            tap = np.concatenate((np.linspace(0,1,n), np.ones(dat.shape[0]-2*n), np.linspace(1,0,n))).astype(dat.dtype)
                            for i in range(channels):
                                dat[:,i] = np.multiply(dat[:,i], tap)

                        # apply the user-specified scaling
                        if scaling_method == 'multiply':
                            dat *= scaling
                        elif scaling_method == 'divide':
                            dat /= scaling
                        elif scaling_method == 'db':
                            dat *= np.power(10., scaling/20.)

                        if np.min(dat)<-1 or np.max(dat)>1:
                            monitor.warning('WARNING: signal exceeds [-1,+1] range, the audio will clip')

                        with lock:
                            # replace the current playback stack
                            stack = dat
                            current_channel = self.redischannel
                            current_value = val
                            # send a trigger to indicate that the sample started playing
                            patch.setvalue("%s.%s" % (started, current_channel), current_value)


# create the background threads that deal with the triggers
trigger = []
for channel, sample in zip(input_channel, input_sample):
    monitor.info(channel, sample)
    trigger.append(TriggerThread(channel, sample))

for thread in trigger:
    thread.start()

# open audio stream
stream = p.open(format=pyaudio.paFloat32,
                channels=channels,
                rate=rate,
                output=True,
                output_device_index=device,
                stream_callback=callback)

# start the output stream
stream.start_stream()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general','delay'))


except (SystemExit, KeyboardInterrupt):
    stream.stop_stream()
    stream.close()
    p.terminate()
    for thread in trigger:
        thread.stop()
    r.publish('SAMPLER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
