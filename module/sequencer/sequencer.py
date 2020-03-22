#!/usr/bin/env python

# This module implements a basic monophonic sequencer
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
debug   = patch.getint('general', 'debug')
clock   = patch.getstring('sequence', 'clock') # the clock signal for the sequence
prefix  = patch.getstring('output', 'prefix')

# these scale and offset parameters are used to map between Redis and internal values
scale_active     = patch.getfloat('scale', 'active',     default=127)
scale_transpose  = patch.getfloat('scale', 'transpose',  default=127)
scale_note       = patch.getfloat('scale', 'note',       default=1)
scale_duration   = patch.getfloat('scale', 'duration',   default=1)
offset_active    = patch.getfloat('offset', 'active',    default=0)
offset_transpose = patch.getfloat('offset', 'transpose', default=0)
offset_note      = patch.getfloat('offset', 'note',      default=0)
offset_duration  = patch.getfloat('offset', 'duration',  default=0)

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()


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
                        monitor.info("step %2d : %s = %g" % (self.step + 1, self.key, val))
                        # increment to the next step
                        self.step = (self.step + 1) % len(self.sequence)


# the notes will be sent to Redis using this key
key = "{}.note".format(prefix)

# create and start the thread for the output
sequencethread = SequenceThread(clock, key)
sequencethread.start()

monitor.update('scale_active',     scale_active)
monitor.update('scale_transpose',  scale_transpose)
monitor.update('scale_note',       scale_note)
monitor.update('scale_duration',   scale_duration)
monitor.update('offset_active',    offset_active)
monitor.update('offset_transpose', offset_transpose)
monitor.update('offset_note',      offset_note)
monitor.update('offset_duration',  offset_duration)

try:
    while True:
        monitor.loop()

        # measure the time to correct for the slip
        start = time.time()

        # the active sequence is specified as an integer between 0 and 127
        active = patch.getfloat('sequence', 'active', default=0)
        active = EEGsynth.rescale(active, slope=scale_active, offset=offset_active)
        active = int(active)

        # get the corresponding sequence as a list
        sequence = "sequence%03d" % (active)
        sequence = patch.getstring('sequence', sequence, multiple=True)

        transpose = patch.getfloat('sequence', 'transpose', default=0.)
        transpose = EEGsynth.rescale(transpose, slope=scale_transpose, offset=offset_transpose)

        # the duration is relative to the time between clock ticks
        duration = patch.getfloat('sequence', 'duration', default=0.)
        duration = EEGsynth.rescale(duration, slope=scale_duration, offset=offset_duration)
        if duration > 0:
            # a duration of 0 or less means that the note will not switch off
            duration = EEGsynth.limit(duration, 0.1, 0.9)

        # show the parameters whose value has changed
        monitor.update("active",    active)
        monitor.update("sequence",  sequence)
        monitor.update("transpose", transpose)
        monitor.update("duration",  duration)

        sequencethread.setSequence(sequence)
        sequencethread.setTranspose(transpose)
        sequencethread.setDuration(duration)

        elapsed = time.time() - start
        naptime = patch.getfloat('general', 'delay') - elapsed
        if naptime > 0:
            time.sleep(naptime)

except KeyboardInterrupt:
    try:
        monitor.success("Disabling last note")
        patch.setvalue(key, 0.)
    except:
        pass
    monitor.success('Closing threads')
    sequencethread.stop()
    r.publish('SEQUENCER_UNBLOCK', 1)
    sequencethread.join()
    sys.exit()
