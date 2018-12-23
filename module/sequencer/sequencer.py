#!/usr/bin/env python

# This module implements a basic monophonic sequencer
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

import ConfigParser  # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
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
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
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

# these scale and offset parameters are used to map between Redis and internal values
scale_active     = patch.getfloat('scale', 'active',     default=127.)
scale_transpose  = patch.getfloat('scale', 'transpose',  default=127.)
scale_note       = patch.getfloat('scale', 'note',       default=1.)
scale_duration   = patch.getfloat('scale', 'duration',   default=1.)
offset_active    = patch.getfloat('offset', 'active',    default=0.)
offset_transpose = patch.getfloat('offset', 'transpose', default=0.)
offset_note      = patch.getfloat('offset', 'note',      default=0.)
offset_duration  = patch.getfloat('offset', 'duration',  default=0.)

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print key, "=", val
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}

class SequenceThread(threading.Thread):
    def __init__(self, redischannel, key):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.key = key
        self.sequence = []
        self.transpose = 0
        self.duration = 0.5
        self.steptime = 0.
        self.prevtime = None
        self.step = 0
        self.running = True

    def setSequence(self, sequence):
        with lock:
            self.sequence = sequence

    def setTranspose(self, transpose):
        with lock:
            self.transpose = transpose

    def setDuration(self, duration):
        with lock:
            self.duration = duration

    def stop(self):
        self.running = False

    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('SEQUENCER_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)    # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    now = time.time()
                    if self.prevtime != None:
                        self.steptime = now - self.prevtime
                    self.prevtime = now
                    if len(self.sequence) > 0:
                        # the sequence can consist of a list of values or a list of Redis channels
                        val = self.sequence[self.step % len(self.sequence)]

                        try:
                            # convert the string from the ini to floating point
                            val = float(val)
                        except:
                            # get the value from Redis
                            val = r.get(val)
                            if val == None:
                                val = 0.
                            else:
                                # convert the string from Redis to floating point
                                val = float(val)

                        # apply the scaling, offset and transpose the note
                        val = EEGsynth.rescale(val, slope=scale_note, offset=offset_note)
                        val += self.transpose
                        # send it as sequencer.note with the note as value
                        patch.setvalue(self.key, val, duration=self.duration*self.steptime)
                        if val>=1.:
                            # send it also as sequencer.noteXXX with value 1.0
                            key = '%s%03d' % (self.key, val)
                            patch.setvalue(key, 1., duration=self.duration*self.steptime)
                        if debug>0:
                            print "step %2d :" % (self.step + 1), self.key, "=", val
                        # increment to the next step
                        self.step = (self.step + 1) % len(self.sequence)


# this is the clock signal for the sequence
clock = patch.getstring('sequence', 'clock')

# the notes will be sent to Redis using this key
key = "{}.note".format(patch.getstring('output', 'prefix'))

# create and start the thread for the output
sequencethread = SequenceThread(clock, key)
sequencethread.start()

if debug > 0:
    show_change('scale_active',     scale_active)
    show_change('scale_transpose',  scale_transpose)
    show_change('scale_note',       scale_note)
    show_change('scale_duration',   scale_duration)
    show_change('offset_active',    offset_active)
    show_change('offset_transpose', offset_transpose)
    show_change('offset_note',      offset_note)
    show_change('offset_duration',  offset_duration)

try:
    while True:
        # measure the time to correct for the slip
        now = time.time()

        if debug > 1:
            print 'loop'

        # the active sequence is specified as an integer between 0 and 127
        active = patch.getfloat('sequence', 'active', default=0)
        active = EEGsynth.rescale(active, slope=scale_active, offset=offset_active)
        active = int(active)

        # get the corresponding sequence as a single string
        try:
            sequence = patch.getstring('sequence', "sequence%03d" % active, multiple=True)
        except:
            sequence = []

        transpose = patch.getfloat('sequence', 'transpose', default=0.)
        transpose = EEGsynth.rescale(transpose, slope=scale_transpose, offset=offset_transpose)

        # the duration is relative to the time between clock ticks
        duration = patch.getfloat('sequence', 'duration', default=0.)
        duration = EEGsynth.rescale(duration, slope=scale_duration, offset=offset_duration)
        duration = EEGsynth.limit(duration, 0.1, 0.9)

        if debug > 0:
            # show the parameters whose value has changed
            show_change("active",    active)
            show_change("sequence",  sequence)
            show_change("transpose", transpose)
            show_change("duration",  duration)

        sequencethread.setSequence(sequence)
        sequencethread.setTranspose(transpose)
        sequencethread.setDuration(duration)

        elapsed = time.time() - now
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime > 0:
            time.sleep(naptime)

except KeyboardInterrupt:
    try:
        print "Disabling last note"
        patch.setvalue(key, 0.)
    except:
        pass
    print "Closing threads"
    sequencethread.stop()
    r.publish('SEQUENCER_UNBLOCK', 1)
    sequencethread.join()
    sys.exit()
