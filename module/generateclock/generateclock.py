#!/usr/bin/env python

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
import mido
from fuzzywuzzy import process
import numpy as np
import os
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
sys.path.insert(0, os.path.join(path,'../../lib'))
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
debug        = patch.getint('general', 'debug')

# the scale and offset are used to map the Redis values to internal values
scale_rate   = patch.getfloat('scale', 'rate')
offset_rate  = patch.getfloat('offset', 'rate')
scale_shift  = patch.getfloat('scale', 'shift')
offset_shift = patch.getfloat('offset', 'shift')
scale_ppqn   = patch.getfloat('scale', 'ppqn')
offset_ppqn  = patch.getfloat('offset', 'ppqn')


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
            monitor.debug('clock beat')
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
                monitor.debug('midi beat')
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
                self.clock = np.mod(np.arange(0, 24, 24/self.ppqn) + self.shift, 24).astype(int)
                monitor.info("redis select = " + str(self.clock))
    def setShift(self, shift):
        if shift != self.shift:
            with lock:
                self.shift = shift
                self.clock = np.mod(np.arange(0, 24, 24/self.ppqn) + self.shift, 24).astype(int)
                monitor.info("redis select = " + str(self.clock))
    def setEnabled(self, enabled):
        self.enabled = enabled
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        while self.running:
            if self.enabled:
                monitor.debug('redis beat')
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
        monitor.loop()

        # measure the time to correct for the slip
        start = time.time()

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
            mididevice = EEGsynth.trimquotes(mididevice)
            mididevice = process.extractOne(mididevice, mido.get_output_names())[0] # select the closest match
            try:
                outputport = mido.open_output(mididevice)
                monitor.success('Connected to MIDI output')
            except:
                raise RuntimeError("cannot connect to MIDI output")

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

        # show the parameters whose value has changed
        monitor.update("redis_play",    redis_play)
        monitor.update("midi_play",     midi_play)
        monitor.update("midi_start",    midi_start)
        monitor.update("rate",          rate)
        monitor.update("shift",         shift)
        monitor.update("ppqn",          ppqn)

        # update the clock and redis
        clockthread.setRate(rate)
        redisthread.setShift(shift)
        redisthread.setPpqn(ppqn)

        elapsed = time.time() - start
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            monitor.trace("naptime =", naptime)
            time.sleep(naptime)

except (KeyboardInterrupt, RuntimeError) as e:
    monitor.success('Closing threads')
    midithread.stop()
    midithread.join()
    redisthread.stop()
    redisthread.join()
    # the thread that manages the clock should be stopped the last
    clockthread.stop()
    clockthread.join()
    sys.exit()
