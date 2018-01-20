#!/usr/bin/env python

# Synchronizer sends a regular clock signal to MIDI, Serial and/or Redis
#
# Synchronizer is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
#
# Copyright (C) 2017-2018 EEGsynth project
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
import math
import mido
import numpy as np
import os
import redis
import serial
import sys
import threading
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

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

serialport = None
def initialize_serial():
    try:
        serialport = serial.Serial(patch.getstring('serial','device'), patch.getint('serial','baudrate'), timeout=3.0)
    except:
        print "Error: cannot connect to serial output"
        exit()
    return serialport

midiport = None
def initialize_midi():
    try:
        midiport = EEGsynth.midiwrapper(config)
        midiport.open_output()
    except:
        print "Error: cannot connect to MIDI output"
        exit()
    return midiport

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class MidiThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
        self.rate = 60
        self.adjust = 0
    def setRate(self, rate):
        lock.acquire()
        self.rate = rate
        lock.release()
    def setAdjust(self, adjust):
        lock.acquire()
        self.adjust = adjust
        lock.release()
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.running = False
    def run(self):
        slip = 0
        msg = mido.Message('clock')
        if debug>0:
            print msg
        while self.running:
            if not self.enabled:
                time.sleep(patch.getfloat('general', 'delay'))
            else:
                now = time.time()
                if debug>0:
                    print 'midi tick'
                delay = 60/self.rate      # the rate is in bpm
                delay -= slip             # correct for the slip from the previous iteration
                jiffy = delay/(24)
                for iteration in range(24):
                    midiport.send(msg)
                    time.sleep(jiffy)
                # the time used in this loop will be slightly different than desired
                slip = time.time() - now - delay

class SerialThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
        self.rate = 60
        self.adjust = 0
    def setRate(self, rate):
        lock.acquire()
        self.rate = rate
        lock.release()
    def setAdjust(self, adjust):
        lock.acquire()
        self.adjust = adjust
        lock.release()
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if not self.enabled:
                time.sleep(patch.getfloat('general', 'delay'))
            else:
                now = time.time()
                if debug>0:
                    print 'serial tick'
                serialport.write('*g1v1#')      # enable the analog gate
                time.sleep(pulselength)         # sleep for the duration of the pulse
                serialport.write('*g1v0#')      # disable the analog gate
                delay = 60/self.rate            # the rate is in bpm
                elapsed = time.time() - now
                time.sleep(delay - elapsed)

class RedisThread(threading.Thread):
    def __init__(self, key):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
        self.rate = 60
        self.adjust = 0
        self.key = key
        self.value = 1.0
    def setRate(self, rate):
        lock.acquire()
        self.rate = rate
        lock.release()
    def setAdjust(self, adjust):
        lock.acquire()
        self.adjust = adjust
        lock.release()
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if not self.enabled:
                time.sleep(patch.getfloat('general', 'delay'))
            else:
                now = time.time()
                if debug>0:
                    print 'redis tick'
                r.publish(self.key, self.value) # send it as trigger
                delay = 60/self.rate            # the rate is in bpm
                elapsed = time.time() - now
                time.sleep(delay - elapsed)

# these will only be started when needed
init_midi   = False
init_serial = False

previous_use_midi   = None
previous_use_serial = None
previous_use_redis  = None

# this is for the analog trigger, expressed in seconds
pulselength = patch.getfloat('general', 'pulselength')

# start the threads for the synchronization
midisync = MidiThread()
midisync.start()
serialsync = SerialThread()
serialsync.start()
redissync = RedisThread(patch.getstring('output', 'prefix'))
redissync.start()

try:
    while True:
        if debug>0:
            print 'loop'

        # measure the time to correct for the slip
        now = time.time()

        use_midi   = patch.getint('general', 'midi', default=0)
        use_serial = patch.getint('general', 'serial', default=0)
        use_redis  = patch.getint('general', 'redis', default=0)

        if previous_use_midi is None:
            previous_use_midi = not(use_midi);

        if previous_use_serial is None:
            previous_use_serial = not(use_serial);

        if previous_use_redis is None:
            previous_use_redis = not(use_redis);

        if use_midi and not init_midi:
            # this might not be running at the start
            midiport = initialize_midi()
            init_midi = True

        if use_serial and not init_serial:
            # this might not be running at the start
            serialport = initialize_serial()
            init_serial = True

        if use_midi and not previous_use_midi:
            midisync.enable()
            previous_use_midi = True
        elif not use_midi and previous_use_midi:
            midisync.disable()
            previous_use_midi = False

        if use_serial and not previous_use_serial:
            serialsync.enable()
            previous_use_serial = True
        elif not use_serial and previous_use_serial:
            serialsync.disable()
            previous_use_serial = False

        if use_redis and not previous_use_redis:
            redissync.enable()
            previous_use_redis = True
        elif not use_redis and previous_use_redis:
            redissync.disable()
            previous_use_redis = False

        rate = patch.getfloat('input', 'rate', default=60/127)
        scale_rate = patch.getfloat('scale', 'rate', default=127)
        offset_rate = patch.getfloat('offset', 'rate', default=0)
        rate = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)

        adjust = patch.getfloat('input', 'adjust', default=0)
        scale_adjust = patch.getfloat('scale', 'adjust', default=2)
        offset_adjust = patch.getfloat('offset', 'adjust', default=-1)
        adjust = EEGsynth.rescale(adjust, slope=scale_adjust, offset=offset_adjust)

        # map the adjust value to zero when very small
        if abs(adjust)<0.01:
            adjust = 0;

        multiply = patch.getfloat('input', 'multiply', default=0.5)
        scale_multiply = patch.getfloat('scale', 'multiply', default=4)
        offset_multiply = patch.getfloat('offset', 'multiply', default=-2.015748031495)
        multiply = EEGsynth.rescale(multiply, slope=scale_multiply, offset=offset_multiply)

        # map the multiply value exponentially, i.e. -1 becomes 1/2, 0 becomes 1, 1 becomes 2
        multiply = math.pow(2, multiply)
        # it should be 1, 2, 3, 4 or 1/2, 1/3, 1/4, etc
        if multiply>1:
            multiply = round(multiply)
        elif multiply<1:
            multiply = 1.0/round(1.0/multiply);

        if debug>0:
            print "use_midi    = ", use_midi
            print "use_serial  = ", use_serial
            print "use_redis   = ", use_redis
            print "rate        = ", rate
            print "adjust      = ", adjust
            print "multiply    = ", multiply

        if rate>0 and multiply>0:
            # update the synchronization threads
            midisync.setRate(rate*multiply)
            serialsync.setRate(rate*multiply)
            redissync.setRate(rate*multiply)
            midisync.setAdjust(adjust)
            serialsync.setAdjust(adjust)
            redissync.setAdjust(adjust)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            time.sleep(naptime)

except KeyboardInterrupt:
    print "Closing threads"
    midisync.stop()
    serialsync.stop()
    redissync.stop()
    midisync.join()
    serialsync.join()
    redissync.join()
    sys.exit()
