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

try:
    # Python 2
    import configparser as configparser
except ImportError:
    # Python 3
    import ConfigParser as configparser

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

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print("Error: cannot connect to redis server")
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# these are for mapping the Redis values to internal values
scale_rate   = patch.getfloat('scale', 'rate')
offset_rate  = patch.getfloat('offset', 'rate')
scale_shift  = patch.getfloat('scale', 'shift')
offset_shift = patch.getfloat('offset', 'shift')
scale_ppqn   = patch.getfloat('scale', 'ppqn')
offset_ppqn  = patch.getfloat('offset', 'ppqn')


# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print(key, "=", val)
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}


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
                print('clock beat')
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
        self.enables = False
        self.running = False
    def run(self):
        msg = mido.Message('clock')
        while self.running:
            if self.enabled and midiport:
                if debug>1:
                    print('midi beat')
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
        self.ppqn     = 1      # this determines how many messages are sent per quarter note
        self.shift    = 0      # this determines by how many ticks the Redis message is shifted
        self.clock    = [0]    # it will send a message on the selected clock ticks
        self.key      = "{}.note".format(patch.getstring('output', 'prefix'))
    def setPpqn(self, ppqn):
        if ppqn != self.ppqn:
            with lock:
                self.ppqn = ppqn
                self.clock = np.mod(np.arange(0, 24, 24/self.ppqn) + self.shift, 24)
                if debug>0:
                    print("redis select =", self.clock)
    def setShift(self, shift):
        if shift != self.shift:
            with lock:
                self.shift = shift
                self.clock = np.mod(np.arange(0, 24, 24/self.ppqn) + self.shift, 24)
                if debug>0:
                    print("redis select =", self.clock)
    def setEnabled(self, enabled):
        self.enabled = enabled
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        while self.running:
            if self.enabled:
                if debug>1:
                    print('redis beat')
                for tick in [clock[indx] for indx in self.clock]:
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

previous_midi_play   = None
previous_midi_start  = None
previous_redis_play  = None

try: # FIXME do we need this or can we catch errors before?
    while True:
        # measure the time to correct for the slip
        now = time.time()

        if debug>3:
            print('loop')

        redis_play  = patch.getint('redis', 'play')
        midi_play   = patch.getint('midi', 'play')
        midi_start  = patch.getint('midi', 'start')

        if previous_redis_play is None and redis_play is not None:
            previous_redis_play = not(redis_play)

        if previous_midi_play is None and midi_play is not None:
            previous_midi_play = not(midi_play)

        if previous_midi_start is None and midi_start is not None:
            previous_midi_start = not(midi_start)

        # the MIDI port should only be opened once, and only if needed
        if midi_play and midiport == None:
            mididevice = patch.getstring('midi', 'device')
            try:
                outputport  = mido.open_output(mididevice)
                if debug>0:
                    print("Connected to MIDI output")
            except:
                print("Error: cannot connect to MIDI output")
                exit()

        # do something whenever the value changes
        if redis_play and not previous_redis_play:
            redisthread.setEnabled(True)
            previous_redis_play = True
        elif not redis_play and previous_redis_play:
            redisthread.setEnabled(False)
            previous_redis_play = False

        # do something whenever the value changes
        if midi_play and not previous_midi_play:
            midithread.setEnabled(True)
            previous_midi_play = True
        elif not midi_play and previous_midi_play:
            midithread.setEnabled(False)
            previous_midi_play = False

        # do something whenever the value changes
        if midi_start and not previous_midi_start:
            if midiport != None:
                midiport.send(mido.Message('start'))
            previous_midi_start = True
        elif not midi_start and previous_midi_start:
            if midiport != None:
                midiport.send(mido.Message('stop'))
            previous_midi_start = False

        rate  = patch.getfloat('input', 'rate', default=0)
        rate  = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
        rate  = EEGsynth.limit(rate, 30., 240.)

        shift = patch.getfloat('input', 'shift', default=0)
        shift = EEGsynth.rescale(shift, slope=scale_shift, offset=offset_shift)
        shift = int(shift)

        ppqn  = patch.getfloat('input', 'ppqn', default=0)
        ppqn  = EEGsynth.rescale(ppqn, slope=scale_ppqn, offset=offset_ppqn)
        ppqn  = find_nearest_value([1, 2, 3, 4, 6, 8, 12, 24], ppqn)

        if debug>0:
            # show the parameters whose value has changed
            show_change("redis_play",    redis_play)
            show_change("midi_play",     midi_play)
            show_change("midi_start",    midi_start)
            show_change("rate",          rate)
            show_change("shift",         shift)
            show_change("ppqn",          ppqn)

        # update the clock and redis
        clockthread.setRate(rate)
        redisthread.setShift(shift)
        redisthread.setPpqn(ppqn)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            if debug>3:
                print("naptime =", naptime)
            time.sleep(naptime)

except (KeyboardInterrupt, RuntimeError) as e:
    print("Closing threads")
    midithread.stop()
    midithread.join()
    redisthread.stop()
    redisthread.join()
    # the thread that manages the clock should be stopped the last
    clockthread.stop()
    clockthread.join()
    sys.exit()
