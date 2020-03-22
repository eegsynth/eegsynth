#!/usr/bin/env python

# Synthesizer acts as a very basic software audio synthesizer
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
import math
import multiprocessing
import os
import pyaudio
import redis
import sys
import threading
import time

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
debug = patch.getint('general', 'debug')

p = pyaudio.PyAudio()

device = patch.getint('audio', 'device')
rate = patch.getint('audio', 'rate')
blocksize = patch.getint('audio', 'blocksize')
nchans = 1
format = p.get_format_from_width(2)  # the desired sample width in bytes (1, 2, 3, or 4)

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

stream = p.open(format=format,
                channels=nchans,
                rate=rate,
                output=True,
                output_device_index=device)

lock = threading.Lock()


class TriggerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        lock.acquire()
        self.time = 0
        self.last = 0
        lock.release()

    def stop(self):
        self.running = False

    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('SYNTHESIZER_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(patch.getstring('control', 'adsr_gate'))
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                monitor.debug(item['channel'], "=", item['data'])
                lock.acquire()
                self.last = self.time
                lock.release()


class ControlThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        lock.acquire()
        self.vco_pitch = 0
        self.vco_sin = 0
        self.vco_tri = 0
        self.vco_saw = 0
        self.vco_sqr = 0
        self.lfo_depth = 0
        self.lfo_frequency = 0
        self.adsr_attack = 0
        self.adsr_decay = 0
        self.adsr_sustain = 0
        self.adsr_release = 0
        self.vca_envelope = 0
        lock.release()

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            ################################################################################
            # these are to map the Redis values to MIDI values
            ################################################################################
            scale_vco_pitch = patch.getfloat('scale', 'vco_pitch')
            offset_vco_pitch = patch.getfloat('offset', 'vco_pitch')

            ################################################################################
            # VCO
            ################################################################################
            vco_pitch = patch.getfloat('control', 'vco_pitch', default=60)
            vco_sin = patch.getfloat('control', 'vco_sin', default=0.75)
            vco_tri = patch.getfloat('control', 'vco_tri', default=0.00)
            vco_saw = patch.getfloat('control', 'vco_saw', default=0.25)
            vco_sqr = patch.getfloat('control', 'vco_sqr', default=0.00)

            # map the Redis values to MIDI values
            vco_pitch = EEGsynth.rescale(vco_pitch, scale_vco_pitch, offset_vco_pitch)

            vco_total = vco_sin + vco_tri + vco_saw + vco_sqr
            if vco_total > 0:
                # these are all scaled relatively to each other
                vco_sin = vco_sin / vco_total
                vco_tri = vco_tri / vco_total
                vco_saw = vco_saw / vco_total
                vco_sqr = vco_sqr / vco_total

            ################################################################################
            # LFO
            ################################################################################
            lfo_frequency = patch.getfloat('control', 'lfo_frequency', default=2)
            lfo_depth = patch.getfloat('control', 'lfo_depth', default=0.5)

            ################################################################################
            # ADSR
            ################################################################################
            adsr_attack = patch.getfloat('control', 'adsr_attack', default=0.25)
            adsr_decay = patch.getfloat('control', 'adsr_decay', default=0.25)
            adsr_sustain = patch.getfloat('control', 'adsr_sustain', default=0.5)
            adsr_release = patch.getfloat('control', 'adsr_release', default=0.25)

            # convert from value between 0 and 1 into time in samples
            adsr_attack *= float(rate)
            adsr_decay *= float(rate)
            adsr_sustain *= float(rate)
            adsr_release *= float(rate)

            ################################################################################
            # VCA
            ################################################################################
            vca_envelope = patch.getfloat('control', 'vca_envelope', default=0.5)

            ################################################################################
            # store the control values in the local object
            ################################################################################
            lock.acquire()
            self.vco_pitch = vco_pitch
            self.vco_sin = vco_sin
            self.vco_tri = vco_tri
            self.vco_saw = vco_saw
            self.vco_sqr = vco_sqr
            self.lfo_depth = lfo_depth
            self.lfo_frequency = lfo_frequency
            self.adsr_attack = adsr_attack
            self.adsr_decay = adsr_decay
            self.adsr_sustain = adsr_sustain
            self.adsr_release = adsr_release
            self.vca_envelope = vca_envelope
            lock.release()

            monitor.trace('----------------------------------')
            monitor.trace('vco_pitch      =', vco_pitch)
            monitor.trace('vco_sin        =', vco_sin)
            monitor.trace('vco_tri        =', vco_tri)
            monitor.trace('vco_saw        =', vco_saw)
            monitor.trace('vco_sqr        =', vco_sqr)
            monitor.trace('lfo_depth      =', lfo_depth)
            monitor.trace('lfo_frequency  =', lfo_frequency)
            monitor.trace('adsr_attack    =', adsr_attack)
            monitor.trace('adsr_decay     =', adsr_decay)
            monitor.trace('adsr_sustain   =', adsr_sustain)
            monitor.trace('adsr_release   =', adsr_release)
            monitor.trace('vca_envelope   =', vca_envelope)


# start the background thread that deals with control value changes
control = ControlThread()
control.start()

# start the background thread that deals with triggers
trigger = TriggerThread()
trigger.start()

block = 0
offset = 0

try:
    while True:
        monitor.loop()

        ################################################################################
        # this is constantly generating the output signal
        ################################################################################
        BUFFER = ''

        for t in range(offset, offset + blocksize):
            # update the time for the trigger detection

            lock.acquire()
            trigger.time = t
            last = trigger.last
            vco_pitch = control.vco_pitch
            vco_sin = control.vco_sin
            vco_tri = control.vco_tri
            vco_saw = control.vco_saw
            vco_sqr = control.vco_sqr
            lfo_depth = control.lfo_depth
            lfo_frequency = control.lfo_frequency
            adsr_attack = control.adsr_attack
            adsr_decay = control.adsr_decay
            adsr_sustain = control.adsr_sustain
            adsr_release = control.adsr_release
            vca_envelope = control.vca_envelope
            lock.release()

            # compose the VCO waveform
            if vco_pitch > 0:
                # note 60 on the keyboard is the C4, which is 261.63 Hz
                # note 72 on the keyboard is the C5, which is 523.25 Hz
                frequency = math.pow(2, (vco_pitch / 12 - 4)) * 261.63
                period = rate / frequency
                wave_sin = vco_sin * (math.sin(math.pi * frequency * t / rate) + 1) / 2
                wave_tri = vco_tri * float(abs(t % period - period / 2)) / period * 2
                wave_saw = vco_saw * float(t % period) / period
                wave_sqr = vco_sqr * float((t % period) > period / 2)
                waveform = (wave_sin + wave_tri + wave_saw + wave_sqr) * 127
            else:
                waveform = 0

            # compose and apply the LFO
            lfo_envelope = (math.sin(math.pi * lfo_frequency * t / rate) + 1) / 2
            lfo_envelope = lfo_depth + (1 - lfo_depth) * lfo_envelope
            waveform = lfo_envelope * waveform

            # compose and apply the ADSR
            if adsr_attack > 0 and (t - last) < adsr_attack:
                adsr_envelope = (t - last) / adsr_attack
            elif adsr_decay > 0 and (t - last - adsr_attack) < adsr_decay:
                adsr_envelope = 1.0 - 0.5 * (t - last - adsr_attack) / adsr_decay
            elif adsr_sustain > 0 and (t - last - adsr_attack - adsr_decay) < adsr_sustain:
                adsr_envelope = 0.5
            elif adsr_release > 0 and (t - last - adsr_attack - adsr_decay - adsr_sustain) < adsr_release:
                adsr_envelope = 0.5 - 0.5 * (t - last - adsr_attack - adsr_decay - adsr_sustain) / adsr_release
            else:
                adsr_envelope = 0
            waveform = adsr_envelope * waveform

            # apply the VCA
            waveform = vca_envelope * waveform

            # add the current waveform sample to the buffer
            BUFFER = BUFFER + chr(int(waveform))

        # write the buffer content to the audio device
        stream.write(BUFFER)
        offset = offset + blocksize

except KeyboardInterrupt:
    monitor.success('Closing threads')
    control.stop()
    control.join()
    trigger.stop()
    r.publish('SYNTHESIZER_UNBLOCK', 1)
    trigger.join()
    stream.stop_stream()
    stream.close()
    p.terminate()
