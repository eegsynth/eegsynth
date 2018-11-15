#!/usr/bin/env python

# Sequencer acts as a basic timer and sequencer
#
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

import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import argparse
import math
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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# this can be used to selectively show parameters that have changed
previous = {}
def show_change(key, val):
    if (key in previous and previous[key]!=val) or (key not in previous):
        print key, "=", val
    previous[key] = val

# this is to prevent two threads accesing a variable at the same time
lock = threading.Lock()

clock = []
for iteration in range(24):
    clock.append(threading.Event())

class ClockThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.rate = 60              # the rate is in bpm, i.e. quarternotes per minute
    def setRate(self, rate):
        with lock:
            self.rate = rate
    def stop(self):
        self.running = False
    def run(self):
        slip = 0
        while self.running:
            now    = time.time()
            delay  = 60/self.rate   # the rate is in bpm
            delay -= slip           # correct for the slip from the previous iteration
            jiffy = delay/(24)
            if debug>1:
                print 'clock step'
            for iteration in range(24):
                clock[iteration].set()
                clock[iteration].clear()
                if jiffy>0:
                    time.sleep(jiffy)
            # the actual time used in this loop will be slightly different than desired
            # this will be corrected on the next iteration
            slip = time.time() - now - delay

class SequenceThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running   = True
        self.steps     = 0
        self.adjust    = 0
        self.sequence  = []
        self.transpose = 0
        self.current   = 0
    def setSteps(self, steps):
        with lock:
            self.steps = steps
    def setAdjust(self, adjust):
        with lock:
            self.adjust = adjust
    def setSequence(self, sequence):
        with lock:
            self.sequence = sequence
    def setTranspose(self, transpose):
        with lock:
            self.transpose = transpose
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if self.steps in [1, 2, 3, 4, 6, 8, 12, 24] and len(self.sequence):
                with lock:
                    step = np.mod(np.arange(0, 24, 24/self.steps) + self.adjust, 24).astype(int).tolist()
                if debug>1:
                    print "sequence step =", step

                for tick in [clock[i] for i in step]:
                    # the note can be a value or a string pointing to a Redis channel
                    with lock:
                        if len(self.sequence):
                            note = self.sequence[np.mod(self.current, len(self.sequence))]
                        else:
                            note = None
                    note = r.get(note) or note
                    try:
                        note = float(note)
                    except TypeError:
                        # this happens if it is not a number or a string, e.g. None
                        note = None
                    except ValueError:
                        # this happens if it is a string that cannot be converted
                        note = None
                    if note:
                        # map the Redis values to the internally used values
                        note = EEGsynth.rescale(note, slope=pattern_scale, offset=pattern_offset)
                        note = note + self.transpose
                        # map the internally used values to Redis values
                        val = EEGsynth.rescale(note, slope=output_scale, offset=output_offset)
                    if debug>1:
                        print 'sequence note =', note
                    tick.wait()             # wait for synchronization with the clock thread
                    if note:
                        r.set(key, val)     # send it as control value
                        r.publish(key, val) # send it as trigger
                    self.current += 1
            else:
                # if self.steps is not appropriate
                time.sleep(patch.getfloat('general', 'delay'))

# create and start the thread that manages the clock
clockthread = ClockThread()
clockthread.start()

# create and start the thread for the output
sequencethread = SequenceThread()
sequencethread.start()

# these scale and offset parameters are used to map Redis values to internal values
scale_pattern    = patch.getfloat('scale', 'pattern',   default=127.) # internal MIDI values
scale_rate       = patch.getfloat('scale', 'rate',      default=127.) # beats per minute
scale_transpose  = patch.getfloat('scale', 'transpose', default=127.) # internal MIDI values
scale_steps      = patch.getfloat('scale', 'steps',     default=1.)
scale_adjust     = patch.getfloat('scale', 'adjust',    default=1.)

offset_pattern   = patch.getfloat('offset', 'pattern',   default=0.)
offset_rate      = patch.getfloat('offset', 'rate',      default=0.)
offset_transpose = patch.getfloat('offset', 'transpose', default=0.)
offset_steps     = patch.getfloat('offset', 'steps',     default=0.)
offset_adjust    = patch.getfloat('offset', 'adjust',    default=0.)

# the output scale and offset are used to map the internal values to Redis values
pattern_scale  = patch.getfloat('output', 'scale', default=127.)
pattern_offset = patch.getfloat('output', 'offset', default=0.)

# the output scale and offset are used to map the internal values to Redis values
output_scale  = patch.getfloat('output', 'scale', default=1./127)
output_offset = patch.getfloat('output', 'offset', default=0.)

# the notes will be sent to Redis using this key
key = "{}.note".format(patch.getstring('output','prefix'))

if debug>0:
    show_change('scale_pattern',    scale_pattern)
    show_change('scale_transpose',  scale_transpose)
    show_change('scale_rate',       scale_rate)
    show_change('scale_steps',      scale_steps)
    show_change('scale_adjust',     scale_adjust)
    show_change('offset_pattern',   offset_pattern)
    show_change('offset_transpose', offset_transpose)
    show_change('offset_rate',      offset_rate)
    show_change('offset_steps',     offset_steps)
    show_change('offset_adjust',    offset_adjust)

try:
    while True:
        # measure the time to correct for the slip
        now = time.time()

        if debug>0:
            print 'loop'

        # the pattern should be a integer between 0 and 127
        pattern = patch.getfloat('control','pattern', default=0)
        pattern = EEGsynth.rescale(pattern, slope=scale_pattern, offset=offset_pattern)
        pattern = int(pattern)

        # use a default rate of 90 bpm
        rate = patch.getfloat('control','rate', default=90./127)
        rate = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)
        # ensure that the rate is within meaningful limits
        rate = EEGsynth.limit(rate, 40., 240.)

        # use a default transposition of 48
        transpose = patch.getfloat('control','transpose', default=48./127)
        transpose = EEGsynth.rescale(transpose, slope=scale_transpose, offset=offset_transpose)

        steps = patch.getfloat('control', 'steps', default=1)
        steps = EEGsynth.rescale(steps, slope=scale_steps, offset=offset_steps)
        steps = int(steps)

        adjust = patch.getfloat('control', 'adjust', default=0)
        adjust = EEGsynth.rescale(adjust, slope=scale_adjust, offset=offset_adjust)
        adjust = int(adjust)

        # get the corresponding sequence as a single string
        try:
            sequence = patch.getstring('sequence',"pattern{:d}".format(pattern))
        except:
            sequence = ''
        if sequence.find(",") > -1:
            separator = ","
        else:
            separator = " "
        # convert the single string into a list
        sequence = sequence.split(separator)
        # remove the empty items, e.g. spaces
        sequence = filter(len, sequence)

        if debug>0:
            # show the parameters whose value has changed
            show_change("pattern",   pattern)
            show_change("sequence",  sequence)
            show_change("rate",      rate)
            show_change("transpose", transpose)
            show_change("steps",     steps)
            show_change("adjust",    adjust)

        sequencethread.setSequence(sequence)
        clockthread.setRate(rate)
        sequencethread.setTranspose(transpose)
        sequencethread.setSteps(steps)
        sequencethread.setAdjust(adjust)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime>0:
            time.sleep(naptime)

except KeyboardInterrupt:
    try:
        print "Disabling last note"
        r.set(key,0)
        r.publish(key,0)
    except:
        pass
    print "Closing threads"
    sequencethread.stop()
    sequencethread.join()
    # the thread that manages the clock should be stopped the last
    clockthread.stop()
    clockthread.join()
    sys.exit()
