#!/usr/bin/env python

# Endorphines interfaces with the Endorphines Cargo MIDI-to-CV device
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
import mido
from fuzzywuzzy import process
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
debug      = patch.getint('general', 'debug')
mididevice = patch.getstring('midi', 'device')
mididevice = EEGsynth.trimquotes(mididevice)
mididevice = process.extractOne(mididevice, mido.get_output_names())[0] # select the closest match

# this is only for debugging, check which MIDI devices are accessible
monitor.info('------ OUTPUT ------')
for port in mido.get_output_names():
  monitor.info(port)
monitor.info('-------------------------')

try:
    outputport = mido.open_output(mididevice)
    monitor.success('Connected to MIDI output')
except:
    raise RuntimeError("cannot connect to MIDI output")

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, midichannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.midichannel = midichannel
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('ENDORPHINES_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)      # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    monitor.info(item)
                    if int(float(item['data']))>0:
                        pitch = int(8191)
                    else:
                        pitch = int(0)
                    msg = mido.Message('pitchwheel', pitch=pitch, channel=self.midichannel)
                    monitor.debug(msg)
                    lock.acquire()
                    outputport.send(msg)
                    lock.release()
                    # keep it at the present value for a minimal amount of time
                    time.sleep(patch.getfloat('general','pulselength'))

# each of the gates that can be triggered is mapped onto a different message
trigger = []
for channel in range(0, 16):

    # channels are one-offset in the ini file, zero-offset in the code
    name = 'channel{}'.format(channel+1)
    if config.has_option('gate', name):

        # start the background thread that deals with this channel
        this = TriggerThread(patch.getstring('gate', name), channel)
        trigger.append(this)
        monitor.debug(name, 'OK')

# start the thread for each of the notes
for thread in trigger:
    thread.start()

# control values are only relevant when different from the previous value
previous_val = {}
previous_port_val = {}
for channel in range(0, 16):
    name = 'channel{}'.format(channel+1)
    previous_val[name] = None
    previous_port_val[name] = None

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

        # loop over the control values
        for channel in range(0, 16):
            # channels are one-offset in the ini file, zero-offset in the code
            name = 'channel{}'.format(channel+1)
            val = patch.getfloat('control', name)
            port_val  = patch.getfloat('portamento', name, default=0)

            if val is None:
                # the value is not present in Redis, skip it
                monitor.trace(name, 'not available')
                continue

            if port_val is None:
                # the value is not present in Redis, skip it
                monitor.trace(name, 'not available')
                continue

            # the scale and offset options are channel specific
            scale  = patch.getfloat('scale', name, default=1)
            offset = patch.getfloat('offset', name, default=0)

            # map the Redis values to MIDI pitch values
            val = EEGsynth.rescale(val, slope=scale, offset=offset)

            # portamento range is hardcoded 0-127, so no need for user-config
            port_val = EEGsynth.rescale(port_val, slope=127, offset=0)

            # ensure that values are within limits
            if patch.getstring('general', 'mode') == 'note':
                val = EEGsynth.limit(val, lo=0, hi=127)
                val = int(val)
                port_val = EEGsynth.limit(port_val, lo=0, hi=127)
                port_val = int(port_val)
            elif patch.getstring('general', 'mode') == 'pitchbend':
                val = EEGsynth.limit(val, lo=-8192, hi=8191)
                val = int(val)
            else:
                monitor.info('No output mode (note or pitchbend) specified!')
                break

            if val != previous_val[name] or not val: # it should be skipped when identical to the previous value

                previous_val[name] = val

                monitor.info(name, val, port_val)

                # midi channels in the inifile are 1-16, in the code 0-15
                midichannel = channel

                if patch.getstring('general', 'mode') == 'pitchbend':
                    msg = mido.Message('pitchwheel', pitch=val, channel=midichannel)
                elif patch.getstring('general', 'mode') == 'note':
                    msg = mido.Message('note_on', note=val, velocity=127, time=0, channel=midichannel)

                monitor.debug(msg)

                lock.acquire()
                outputport.send(msg)
                lock.release()

                # keep it at the present value for a minimal amount of time
                time.sleep(patch.getfloat('general', 'pulselength'))

            if port_val != previous_port_val[name] and patch.getstring('general', 'mode') != 'note' or not port_val : # it should be skipped when identical to the previous value
                previous_port_val[name] = port_val

                monitor.info(name, val, port_val)

                # CC#5 sets portamento
                msg = mido.Message('control_change', control=5, value=int(port_val), channel=midichannel)

                monitor.debug(msg)

                lock.acquire()
                outputport.send(msg)
                lock.release()

                # keep it at the present value for a minimal amount of time
                time.sleep(patch.getfloat('general', 'pulselength'))

except KeyboardInterrupt:
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('ENDORPHINES_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
