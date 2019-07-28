#!/usr/bin/env python

# This module translates Redis control values and events to MIDI.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2019 EEGsynth project
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

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
monophonic = patch.getint('general', 'monophonic', default=1)

# this is only for debugging, and to check which MIDI devices are accessible
print('------ INPUT ------')
for port in mido.get_input_names():
  print(port)
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

midichannel = patch.getint('midi', 'channel')-1  # channel 1-16 get mapped to 0-15
mididevice = patch.getstring('midi', 'device')
mididevice = EEGsynth.trimquotes(mididevice)

try:
    outputport  = mido.open_output(mididevice)
    if debug>0:
        print("Connected to MIDI output")
except:
    print("Error: cannot connect to MIDI output")
    exit()

# values between 0 and 1 are quite nice for the note duration
scale_duration  = patch.getfloat('scale', 'duration', default=1)
offset_duration = patch.getfloat('offset', 'duration', default=0)
# values around 64 are nice for the note velocity
scale_velocity    = patch.getfloat('scale', 'velocity', default=1)
offset_velocity   = patch.getfloat('offset', 'velocity', default=0)

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

previous_note = None
velocity_note = None
duration_note = None

def UpdateVelocity():
    global velocity_note
    velocity_note = patch.getfloat('velocity', 'note', default=64)
    velocity_note = int(EEGsynth.rescale(velocity_note, slope=scale_velocity, offset=offset_velocity))

def UpdateDuration():
    global duration_note
    duration_note = patch.getfloat('duration', 'note', default=0.100)
    duration_note = EEGsynth.rescale(duration_note, slope=scale_duration, offset=offset_duration)
    # some minimal time is needed for the duration
    duration_note = EEGsynth.limit(duration_note, 0.05, float('Inf'))

# call them once at the start
UpdateVelocity()
UpdateDuration()

def SetNoteOn(note):
    global previous_note
    if monophonic and previous_note != None:
        SetNoteOff(previous_note)
    if debug>1:
        print('SetNoteOn', note)
    # construct the MIDI message
    if midichannel is None:
        msg = mido.Message('note_on', note=note, velocity=velocity_note)
    else:
        msg = mido.Message('note_on', note=note, velocity=velocity_note, channel=midichannel)
    # send the MIDI message
    lock.acquire()
    previous_note = note
    outputport.send(msg)
    lock.release()
    # schedule a timer to switch it off after the specified duration
    t = threading.Timer(duration_note, SetNoteOff, args=[note])
    t.start()


def SetNoteOff(note):
    global previous_note
    if monophonic and previous_note != note:
        # do not switch off notes other than the previous one
        return
    if debug>1:
        print('SetNoteOff', note)
    # construct the MIDI message
    if midichannel is None:
        msg = mido.Message('note_off', note=note, velocity=velocity_note)
    else:
        msg = mido.Message('note_off', note=note, velocity=velocity_note, channel=midichannel)
    # send the MIDI message
    lock.acquire()
    previous_note = None
    outputport.send(msg)
    lock.release()


# send the MIDI message, different messages have slightly different parameters
def sendMidi(name, code, val):
    global previous

    if name == 'pitchwheel':
        # the value should be limited between -8192 to 8191
        val = EEGsynth.limit(val, -8192, 8191)
        val = int(val)
    else:
        # the value should be limited between 0 and 127
        val = EEGsynth.limit(val, 0, 127)
        val = int(val)

    if debug>0:
        print(name, code, val)

    if name.startswith('note'):
        # note_on and note_off messages are dealt with in another function
        SetNoteOn(val)
        return

    if name.startswith('control'):
        if midichannel is None:
            msg = mido.Message('control_change', control=code, value=val)
        else:
            msg = mido.Message('control_change', control=code, value=val, channel=midichannel)
    elif name.startswith('polytouch'):
        if midichannel is None:
            msg = mido.Message('polytouch', note=code, value=val)
        else:
            msg = mido.Message('polytouch', note=code, value=val, channel=midichannel)
    elif name == 'aftertouch':
        if midichannel is None:
            msg = mido.Message('aftertouch', value=val)
        else:
            msg = mido.Message('aftertouch', value=val, channel=midichannel)
    elif name == 'pitchwheel':
        if midichannel is None:
            msg = mido.Message('pitchwheel', pitch=val)
        else:
            msg = mido.Message('pitchwheel', pitch=val, channel=midichannel)
    # the following MIDI messages are not channel specific
    elif name == 'start':
        msg = mido.Message('start')
    elif name == 'continue':
        msg = mido.Message('continue')
    elif name == 'stop':
        msg = mido.Message('stop')
    elif name == 'reset':
        msg = mido.Message('reset')
    # send the MIDI message
    lock.acquire()
    outputport.send(msg)
    lock.release()


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, name, code):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.name = name
        self.code = code
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('OUTPUTMIDI_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)  # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    if debug>1:
                        print(item['channel'], '=', item['data'])
                    # map the Redis values to MIDI values
                    val = item['data']
                    # the scale and offset options are channel specific and can be changed on the fly
                    scale = patch.getfloat('scale', self.name, default=127)
                    offset = patch.getfloat('offset', self.name, default=0)
                    val = EEGsynth.rescale(val, slope=scale, offset=offset)
                    sendMidi(self.name, self.code, val)


trigger_name = []
trigger_code = []
for code in range(1,128):
    trigger_name.append("note%03d" % code)
    trigger_code.append(code)
    trigger_name.append("control%03d" % code)
    trigger_code.append(code)
    trigger_name.append("polytouch%03d" % code)
    trigger_code.append(code)
for name in ['note', 'aftertouch', 'pitchwheel', 'start', 'continue', 'stop', 'reset']:
    trigger_name.append(name)
    trigger_code.append(None)

# each of the Redis message is mapped onto a different MIDI message
trigger = []
for name, code in zip(trigger_name, trigger_code):
    if config.has_option('trigger', name):
        # start the background thread that deals with this note
        this = TriggerThread(patch.getstring('trigger', name), name, code)
        trigger.append(this)
        if debug>1:
            print(name, 'trigger configured')

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

control_name = []
control_code = []
for code in range(1,128):
    control_name.append("note%03d" % code)
    control_code.append(code)
    control_name.append("control%03d" % code)
    control_code.append(code)
    control_name.append("polytouch%03d" % code)
    control_code.append(code)
for name in ['note', 'aftertouch', 'pitchwheel', 'start', 'continue', 'stop', 'reset']:
    control_name.append(name)
    control_code.append(None)

# control values are only interesting when different from the previous value
previous_val = {}
for name in control_name:
    previous_val[name] = None

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        UpdateVelocity()
        UpdateDuration()

        for name, code in zip(control_name, control_code):
            # loop over the control values
            val = patch.getfloat('control', name)
            if val is None:
                continue # it should be skipped when not present in the ini or Redis
            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            previous_val[name] = val

            # the scale and offset options are channel specific and can be changed on the fly
            scale = patch.getfloat('scale', name, default=127)
            offset = patch.getfloat('offset', name, default=0)
            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            sendMidi(name, code, val)


except KeyboardInterrupt:
    print("Closing threads")
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTMIDI_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
