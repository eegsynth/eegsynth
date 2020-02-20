#!/usr/bin/env python

# Volcabeats outputs Redis data via MIDI to the Korg Volca Beats synthesizer
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

# the list of MIDI commands is the only aspect that is specific to the Volca Beats
# see http://media.aadl.org/files/catalog_guides/1445131_chart.pdf
control_name = ['kick_level', 'snare_level', 'lo_tom_level', 'hi_tom_level', 'closed_hat_level', 'open_hat_level', 'clap_level', 'claves_level', 'agogo_level', 'crash_level', 'clap_speed', 'claves_speed', 'agogo_speed', 'crash_speed', 'stutter_time', 'stutter_depth', 'tom_decay', 'closed_hat_decay', 'open_hat_decay', 'hat_gra    in']
control_code = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
note_name = ['kick', 'snare', 'lo_tom', 'hi_tom', 'closed_hat', 'open_hat', 'clap']
note_code = [36, 38, 43, 50, 42, 46, 39]

# get the options from the configuration file
debug = patch.getint('general','debug')

# this is only for debugging, check which MIDI devices are accessible
monitor.info('------ OUTPUT ------')
for port in mido.get_output_names():
  monitor.info(port)
monitor.info('-------------------------')

midichannel = patch.getint('midi', 'channel')-1  # channel 1-16 get mapped to 0-15
mididevice  = patch.getstring('midi', 'device')
mididevice  = EEGsynth.trimquotes(mididevice)
mididevice  = process.extractOne(mididevice, mido.get_output_names())[0] # select the closest match

try:
    outputport = mido.open_output(mididevice)
    monitor.success('Connected to MIDI output')
except:
    raise RuntimeError("cannot connect to MIDI output")

# the scale and offset are used to map Redis values to MIDI values
scale  = patch.getfloat('input', 'scale', default=127)
offset = patch.getfloat('input', 'offset', default=0)

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, note):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.note = note
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('VOLCABEATS_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)     # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    # map the Redis values to MIDI values
                    val = EEGsynth.rescale(item['data'], slope=scale, offset=offset)
                    val = EEGsynth.limit(val, 0, 127)
                    val = int(val)
                    monitor.debug(item['channel'], "=", val)
                    msg = mido.Message('note_on', note=self.note, velocity=val, channel=midichannel)
                    lock.acquire()
                    outputport.send(msg)
                    lock.release()

# each of the notes that can be played is mapped onto a different trigger
trigger = []
for name, code in zip(note_name, note_code):
    if config.has_option('note', name):
        # start the background thread that deals with this note
        this = TriggerThread(patch.getstring('note', name), code)
        trigger.append(this)
        monitor.debug(name, 'OK')

# start the thread for each of the notes
for thread in trigger:
    thread.start()

# control values are only relevant when different from the previous value
previous_val = {}
for name in control_name:
    previous_val[name] = None

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

        for name, cmd in zip(control_name, control_code):
            # loop over the control values
            val = patch.getfloat('control', name)
            if val==None:
                continue # it should be skipped when not present
            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            previous_val[name] = val
            # map the Redis values to MIDI values
            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            val = EEGsynth.limit(val, 0, 127)
            val = int(val)
            msg = mido.Message('control_change', control=cmd, value=val, channel=midichannel)
            monitor.debug(cmd, val, name)
            lock.acquire()
            outputport.send(msg)
            lock.release()

except KeyboardInterrupt:
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('VOLCABEATS_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
