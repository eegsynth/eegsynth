#!/usr/bin/env python

# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
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

# this can be used to selectively show parameters that have changed
previous = {}
def show_change(key, val):
    if (key in previous and previous[key]!=val) or (key not in previous):
        print key, "=", val
    previous[key] = val

def find_nearest_value(list, value):
    # find the value in the list that is the nearest to the desired value
    return min(list, key=lambda x:abs(x-value))

# this is to prevent two threads accesing a variable at the same time
lock = threading.Lock()

# this is to synchronize the clocks
clock = []
for i in range(0, 24):
    clock.append(threading.Event())


class ClockThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.rate = 60              # the rate is in bpm, i.e. quarter notes per minute
    def setRate(self, rate):
        if rate != self.rate:
            with lock:
                self.rate = rate
    def stop(self):
        self.running = False
    def run(self):
        slip = 0
        while self.running:
            if debug>1:
                print 'clock start'
            start  = time.time()
            delay  = 60/self.rate   # the rate is in bpm
            delay -= slip           # correct for the slip from the previous iteration
            jiffy  = delay/24
            for tick in range(24):
                clock[tick].set()
                clock[tick].clear()
                if jiffy>0:
                    time.sleep(jiffy)
            # the actual time used in this loop will be slightly different than desired
            # this will be corrected on the next iteration
            slip = time.time() - start - delay


class MidiThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
    def setEnabled(self, enabled):
        self.enabled = enabled
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        msg = mido.Message('clock')
        while self.running:
            if self.enabled and midiport:
                if debug>1:
                    print 'midi start'
                for tick in clock:
                    tick.wait()
                    midiport.send(msg)
            else:
                time.sleep(patch.getfloat('general', 'delay'))


class RedisThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running  = True
        self.enabled  = False
        self.steps    = 1   # this determines on which of the MIDI clock ticks the Redis message is sent
        self.adjust   = 0   # this determines by how many MIDI clock ticks the Redis message is shifted
        self.select   = [0] # this is the list of indices for the MIDI clock ticks
        self.key      = "{}.note".format(patch.getstring('output','prefix'))
    def setSteps(self, steps):
        if steps != self.steps:
            with lock:
                self.steps = steps
                self.select = np.mod(np.arange(0, 24, 24/self.steps) + self.adjust, 24)
                print "select =", self.select
    def setAdjust(self, adjust):
        if adjust != self.adjust:
            with lock:
                self.adjust = adjust
                self.select = np.mod(np.arange(0, 24, 24/self.steps) + self.adjust, 24)
                print "select =", self.select
    def setEnabled(self, enabled):
        self.enabled = enabled
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        while self.running:
            if self.enabled:
                if debug>1:
                    print 'redis start'
                for tick in [clock[indx] for indx in self.select]:
                    tick.wait()
                    patch.setvalue(self.key, 1.)
            else:
                time.sleep(patch.getfloat('general', 'delay'))


# create and start the thread that manages the clock
clockthread = ClockThread()
clockthread.start()

# create and start the thread for the MIDI output
midithread = MidiThread()
midithread.start()

# create and start the thread for the Redis output
redisthread = RedisThread()
redisthread.start()

# the MIDI interface will only be started when needed
midiport = None

previous_use_midi   = None
previous_use_redis  = None

try:
    while True:
        # measure the time to correct for the slip
        now = time.time()

        if debug>3:
            print 'loop'

        use_midi   = patch.getint('general', 'midi', default=0)
        use_redis  = patch.getint('general', 'redis', default=0)

        if previous_use_midi is None:
            previous_use_midi = not(use_midi);

        if previous_use_redis is None:
            previous_use_redis = not(use_redis);

        if use_midi and midiport == None:
            # the MIDI port should only be opened once needed
            midiport = EEGsynth.midiwrapper(config)
            midiport.open_output()

        if use_midi and not previous_use_midi:
            midithread.setEnabled(True)
            previous_use_midi = True
        elif not use_midi and previous_use_midi:
            midithread.setEnabled(False)
            previous_use_midi = False

        if use_redis and not previous_use_redis:
            redisthread.setEnabled(True)
            previous_use_redis = True
        elif not use_redis and previous_use_redis:
            redisthread.setEnabled(False)
            previous_use_redis = False

        scale_rate  = patch.getfloat('scale', 'rate', default=127)
        offset_rate = patch.getfloat('offset', 'rate', default=0)
        rate        = patch.getfloat('input', 'rate', default=60./127)
        rate        = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
        rate        = EEGsynth.limit(rate, 40., 240.)

        scale_multiply  = patch.getfloat('scale', 'multiply', default=4)
        offset_multiply = patch.getfloat('offset', 'multiply', default=-2.015748031495)
        multiply        = patch.getfloat('input', 'multiply', default=0.5)
        multiply        = EEGsynth.rescale(multiply, slope=scale_multiply, offset=offset_multiply)

        # map the multiply value exponentially, i.e. -1 becomes 1/2, 0 becomes 1, 1 becomes 2
        multiply = math.pow(2, multiply)
        # it should be 1, 2, 3, 4 or 1/2, 1/3, 1/4, etc
        if multiply>1:
            multiply = round(multiply)
        elif multiply<1:
            multiply = 1.0/round(1.0/multiply);

        scale_steps  = patch.getfloat('scale', 'steps', default=1)
        offset_steps = patch.getfloat('offset', 'steps', default=0)
        steps        = patch.getfloat('input', 'steps', default=1)
        steps        = EEGsynth.rescale(steps, slope=scale_steps, offset=offset_steps)
        steps        = find_nearest_value([1, 2, 3, 4, 6, 8, 12, 24], steps)

        scale_adjust  = patch.getfloat('scale', 'adjust', default=1)
        offset_adjust = patch.getfloat('offset', 'adjust', default=0)
        adjust        = patch.getfloat('input', 'adjust', default=0)
        adjust        = EEGsynth.rescale(adjust, slope=scale_adjust, offset=offset_adjust)
        adjust        = int(adjust)

        if debug>0:
            # show the parameters whose value has changed
            show_change("use_midi",      use_midi)
            show_change("use_redis",     use_redis)
            show_change("rate",          rate)
            show_change("multiply",      multiply)
            show_change("steps",         steps)
            show_change("adjust",        adjust)

        # update the clock and redis
        clockthread.setRate(rate * multiply)
        redisthread.setSteps(steps)
        redisthread.setAdjust(adjust)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            if debug>3:
                print "naptime =", naptime
            time.sleep(naptime)

except (KeyboardInterrupt, RuntimeError) as e:
    print "Closing threads"
    midithread.stop()
    midithread.join()
    redisthread.stop()
    redisthread.join()
    # the thread that manages the clock should be stopped the last
    clockthread.stop()
    clockthread.join()
    sys.exit()
