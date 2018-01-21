#!/usr/bin/env python

# Synchronizer sends a regular clock trigger to MIDI, Serial and/or Redis
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

# this can be used to selectively show parameters that have changed
previous = {}
def show_change(key, val):
    if key in previous and previous[key]!=val:
        print key, "=", val
    previous[key] = val

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

event = []
for iteration in range(24):
    event.append(threading.Event())

class ClockThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.rate = 60              # the rate is in bpm, i.e. quarternotes per minute
    def setRate(self, rate):
        lock.acquire()
        self.rate = rate
        lock.release()
    def stop(self):
        self.running = False
    def run(self):
        slip = 0
        while self.running:
            now    = time.time()
            delay  = 60/self.rate     # the rate is in bpm
            delay -= slip             # correct for the slip from the previous iteration
            jiffy = delay/(24)
            if debug>1:
                print 'clock tick'
            for iteration in range(24):
                event[iteration].set()
                event[iteration].clear()
                if jiffy>0:
                    time.sleep(jiffy)
            # the actual time used in this loop will be slightly different than desired
            # this will be corrected on the next iteration
            slip = time.time() - now - delay

class MidiThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        msg = mido.Message('clock')
        while self.running:
            if self.enabled and midiport:
                if debug>1:
                    print 'midi tick'
                for clock in event:
                    clock.wait()
                    midiport.send(msg)

class SerialThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running  = True
        self.enabled  = False
        self.adjust   = 0
        self.steps    = 1
    def setSteps(self, steps):
        with lock:
            self.steps = steps
    def setAdjust(self, adjust):
        with lock:
            self.adjust = adjust
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        while self.running:
            if self.enabled and serialport:
                if self.steps in [1, 2, 3, 4, 6, 8, 12, 24]:
                    with lock:
                        tick = np.mod(np.arange(0, 24, 24/self.steps) + self.adjust, 24).astype(int).tolist()
                    if debug>1:
                        print 'serial tick =', tick
                    for clock in [event[i] for i in tick]:
                        clock.wait()
                        serialport.write('*g1v1#')      # enable the analog gate
                        if pulselength>0:
                            time.sleep(pulselength)
                        serialport.write('*g1v0#')      # disable the analog gate
            else:
                time.sleep(patch.getfloat('general', 'delay'))

class RedisThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running  = True
        self.enabled  = False
        self.adjust   = 0
        self.steps    = 1
        self.key      = patch.getstring('output', 'channel')
        self.value    = 1.0
    def setSteps(self, steps):
        with lock:
            self.steps = steps
    def setAdjust(self, adjust):
        with lock:
            self.adjust = adjust
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.enabled = False
        self.running = False
    def run(self):
        while self.running:
            if self.enabled:
                if self.steps in [1, 2, 3, 4, 6, 8, 12, 24]:
                    with lock:
                        tick = np.mod(np.arange(0, 24, 24/self.steps) + self.adjust, 24)
                    if debug>1:
                        print 'redis tick =', tick
                    for clock in [event[i] for i in tick]:
                        clock.wait()
                        r.publish(self.key, self.value) # send it as trigger
            else:
                time.sleep(patch.getfloat('general', 'delay'))

# these will only be started when needed
init_midi   = False
init_serial = False

previous_use_midi   = None
previous_use_serial = None
previous_use_redis  = None

# create and start the thread for the synchronization
clocksync = ClockThread()
clocksync.start()
# create and start the threads for the output
midisync = MidiThread()
midisync.start()
serialsync = SerialThread()
serialsync.start()
redissync = RedisThread()
redissync.start()

try:
    while True:
        # measure the time to correct for the slip
        now = time.time()

        if debug>0:
            print 'loop'

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

        rate = patch.getfloat('input', 'rate', default=60./127)
        scale_rate = patch.getfloat('scale', 'rate', default=127)
        offset_rate = patch.getfloat('offset', 'rate', default=0)
        rate = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
        # ensure that the rate is within meaningful limits
        rate = EEGsynth.limit(rate, 40., 240.)

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

        # this is for the analog trigger, expressed in seconds
        pulselength = patch.getfloat('general', 'pulselength')
        # ensure the pulselength is within meaningful limits: lowest value is 5 ms, highest value depends on the rate
        pulselength = EEGsynth.limit(pulselength, 0.005, 60./(2*24*rate*multiply))

        steps = patch.getfloat('input', 'steps', default=1)
        scale_steps = patch.getfloat('scale', 'steps', default=1)
        offset_steps = patch.getfloat('offset', 'steps', default=0)
        steps = EEGsynth.rescale(steps, slope=scale_steps, offset=offset_steps)
        steps = int(steps)

        adjust = patch.getfloat('input', 'adjust', default=0)
        scale_adjust = patch.getfloat('scale', 'adjust', default=1)
        offset_adjust = patch.getfloat('offset', 'adjust', default=0)
        adjust = EEGsynth.rescale(adjust, slope=scale_adjust, offset=offset_adjust)
        adjust = int(adjust)

        if debug>0:
            # show the parameters whose value has changed
            show_change("use_midi",      use_midi)
            show_change("use_serial",    use_serial)
            show_change("use_redis",     use_redis)
            show_change("rate",          rate)
            show_change("multiply",      multiply)
            show_change("pulselength",   pulselength)
            show_change("steps",         steps)
            show_change("adjust",        adjust)

        if rate>0 and multiply>0:
            # update the synchronization threads
            clocksync.setRate(rate*multiply)
            redissync.setAdjust(adjust)
            redissync.setSteps(steps)
            serialsync.setAdjust(adjust)
            serialsync.setSteps(steps)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            time.sleep(naptime)

except KeyboardInterrupt:
    print "Closing threads"
    midisync.stop()
    midisync.join()
    serialsync.stop()
    serialsync.join()
    redissync.stop()
    redissync.join()
    # the thread that synchronizes the clocks should be stopped as the last
    clocksync.stop()
    clocksync.join()
    sys.exit()
