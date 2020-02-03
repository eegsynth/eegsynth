#!/usr/bin/env python

# This module receives MIDI events from a keyboard, and that sends MIDI events to the keyboard
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
sys.path.insert(0,os.path.join(path,'../../lib'))
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

# the list of MIDI commands is specific to the implementation for a full-scale keyboard
# see https://newt.phys.unsw.edu.au/jw/notes.html
note_name = ['C0', 'Db0', 'D0', 'Eb0', 'E0', 'F0', 'Gb0', 'G0', 'Ab0', 'A0', 'Bb0', 'B0', 'C1', 'Db1', 'D1', 'Eb1', 'E1', 'F1', 'Gb1', 'G1', 'Ab1', 'A1', 'Bb1', 'B1', 'C2', 'Db2', 'D2', 'Eb2', 'E2', 'F2', 'Gb2', 'G2', 'Ab2', 'A2', 'Bb2', 'B2', 'C3', 'Db3', 'D3', 'Eb3', 'E3', 'F3', 'Gb3', 'G3', 'Ab3', 'A3', 'Bb3', 'B3', 'C4', 'Db4', 'D4', 'Eb4', 'E4', 'F4', 'Gb4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5', 'Db5', 'D5', 'Eb5', 'E5', 'F5', 'Gb5', 'G5', 'Ab5', 'A5', 'Bb5', 'B5', 'C6', 'Db6', 'D6', 'Eb6', 'E6', 'F6', 'Gb6', 'G6', 'Ab6', 'A6', 'Bb6', 'B6', 'C7', 'Db7', 'D7', 'Eb7', 'E7', 'F7', 'Gb7', 'G7', 'Ab7', 'A7', 'Bb7', 'B7', 'C8', 'Db8', 'D8', 'Eb8', 'E8', 'F8', 'Gb8', 'G8', 'Ab8', 'A8', 'Bb8', 'B8', 'C9', 'Db9', 'D9', 'Eb9', 'E9', 'F9', 'Gb9', 'G9', 'Ab9', 'A9', 'Bb9', 'B9', 'C10', 'Db10', 'D10', 'Eb10', 'E10', 'F10', 'Gb10', 'G10', 'Ab10', 'A10', 'Bb10', 'B10']
note_code = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143]

# get the options from the configuration file
debug = patch.getint('general','debug')
midichannel = patch.getint('midi', 'channel', default=None)
mididevice  = patch.getstring('midi', 'device')
mididevice  = EEGsynth.trimquotes(mididevice)
mididevice  = process.extractOne(mididevice, mido.get_input_names())[0] # select the closest match

# the input scale and offset are used to map Redis values to MIDI values
input_scale  = patch.getfloat('input', 'scale', default=127)
input_offset = patch.getfloat('input', 'offset', default=0)

scale_velocity  = patch.getfloat('scale', 'velocity', default=127)
scale_pitch     = patch.getfloat('scale', 'pitch', default=127)
scale_duration  = patch.getfloat('scale', 'duration', default=2.0)
offset_velocity = patch.getfloat('offset', 'velocity', default=0)
offset_pitch    = patch.getfloat('offset', 'pitch', default=0)
offset_duration = patch.getfloat('offset', 'duration', default=0)

# the output scale and offset are used to map MIDI values to Redis values
output_scale  = patch.getfloat('output', 'scale', default=1./127)
output_offset = patch.getfloat('output', 'offset', default=0)

# this is only for debugging, check which MIDI devices are accessible
monitor.info('------ INPUT ------')
for port in mido.get_input_names():
  monitor.info(port)
monitor.info('------ OUTPUT ------')
for port in mido.get_output_names():
  monitor.info(port)
monitor.info('-------------------------')

try:
    inputport = mido.open_input(mididevice)
    monitor.success('Connected to MIDI input')
except:
    raise RuntimeError("cannot connect to MIDI input")

try:
    outputport = mido.open_output(mididevice)
    monitor.success('Connected to MIDI output')
except:
    raise RuntimeError("cannot connect to MIDI output")

# channel 1-16 in the ini file should be mapped to 0-15
if not midichannel is None:
    midichannel-=1
monitor.update('midichannel', midichannel)

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

# this is used to send direct and delayed messages
def SendMessage(msg):
    lock.acquire()
    monitor.info(msg)
    outputport.send(msg)
    lock.release()

class TriggerThread(threading.Thread):
    def __init__(self, onset, velocity, pitch, duration):
        threading.Thread.__init__(self)
        self.onset    = onset    # we will subscribe to this key, the value may be used as velocity
        self.velocity = velocity # optional, this is a value to get
        self.pitch    = pitch    # optional, this is a value to get
        self.duration = duration # optional, this is a value to get
        self.running  = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('KEYBOARD_UNBLOCK')  # this message unblocks the Redis listen command
        pubsub.subscribe(self.onset)      # this message triggers the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.onset:
                    # the trigger may contain a value that should be mapped to MIDI
                    val = float(item['data'])
                    val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
                    val = EEGsynth.limit(val, 0, 127)
                    val = int(val)

                    if self.velocity == None:
                        # use the value of the onset trigger
                        velocity = val
                    elif type(self.velocity) == str:
                        velocity = float(r.get(self.velocity))
                        velocity = EEGsynth.rescale(velocity, slope=scale_velocity, offset=offset_velocity)
                        velocity = EEGsynth.limit(velocity, 0, 127)
                        velocity = int(velocity)
                    else:
                        velocity = self.velocity

                    if type(self.pitch) == str:
                        pitch = float(r.get(self.pitch))
                        pitch = EEGsynth.rescale(pitch, slope=scale_pitch, offset=offset_pitch)
                        pitch = EEGsynth.limit(pitch, 0, 127)
                        pitch = int(pitch)
                    else:
                        pitch = self.pitch

                    if type(self.duration) == str:
                        duration = float(r.get(self.duration))
                        duration = EEGsynth.rescale(duration, slope=scale_duration, offset=offset_duration)
                        duration = EEGsynth.limit(duration, 0.05, float('Inf')) # some minimal time is needed for the delay
                    else:
                        duration = self.duration

                    monitor.debug('----------------------------------------------')
                    monitor.debug("onset   ", self.onset,       "=", val)
                    monitor.debug("velocity", self.velocity,    "=", velocity)
                    monitor.debug("pitch   ", self.pitch,       "=", pitch)
                    monitor.debug("duration", self.duration,    "=", duration)

                    if midichannel is None:
                        msg = mido.Message('note_on', note=pitch, velocity=velocity)
                    else:
                        msg = mido.Message('note_on', note=pitch, velocity=velocity, channel=midichannel)
                    SendMessage(msg)

                    if duration != None:
                        # schedule a delayed MIDI message to be sent to switch the note off
                        if midichannel is None:
                            msg = mido.Message('note_on', note=pitch, velocity=0)
                        else:
                            msg = mido.Message('note_on', note=pitch, velocity=0, channel=midichannel)
                        t = threading.Timer(duration, SendMessage, args=[msg])
                        t.start()

# the keyboard notes can be linked to separate triggers, where the trigger value corresponds to the velocity
trigger = []
for name, code in zip(note_name, note_code):
    if config.has_option('input', name):
        # start the background thread that deals with this note
        onset    = patch.getstring('input', name)
        velocity = None  # use the value of the onset trigger
        pitch    = code
        duration = None
        trigger.append(TriggerThread(onset, velocity, pitch, duration))
        monitor.debug(name, 'OK')

try:
    # the keyboard notes can also be controlled using a single trigger
    onset    = patch.getstring('input', 'onset')
    velocity = patch.getstring('input', 'velocity')
    pitch    = patch.getstring('input', 'pitch')
    duration = patch.getstring('input', 'duration')
    trigger.append(TriggerThread(onset, velocity, pitch, duration))
    monitor.debug('onset, velocity, pitch and duration OK')
except:
    pass

# start the thread for each of the notes
for thread in trigger:
    thread.start()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general','delay'))

        for msg in inputport.iter_pending():
            if midichannel is None:
                try:
                    # specify the MIDI channel on the basis of the first incoming message
                    midichannel = int(msg.channel)
                    monitor.update('midichannel', midichannel)
                except:
                    pass

            if msg.type!='clock':
                monitor.info(msg)

            if hasattr(msg,'note'):
                monitor.info(msg)
                if patch.getstring('processing','detect')=='release' and msg.velocity>0:
                    pass
                elif patch.getstring('processing','detect')=='press' and msg.velocity==0:
                    pass
                else:
                    # prefix.noteXXX=velocity
                    key = '{}.note{:0>3d}'.format(patch.getstring('output','prefix'), msg.note)
                    val = msg.velocity
                    val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
                    patch.setvalue(key, val)
                    # prefix.note=note
                    key = '{}.note'.format(patch.getstring('output','prefix'))
                    val = msg.note
                    patch.setvalue(key, val)
            elif hasattr(msg,'control'):
                # ignore these
                pass
            elif hasattr(msg,'time'):
                # ignore these
                pass

except KeyboardInterrupt:
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('KEYBOARD_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
