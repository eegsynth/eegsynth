#!/usr/bin/env python

# This module translates Redis control values and events to MIDI.
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


def SetNoteOn(note, velocity):
    global previous_note
    if monophonic and previous_note != None:
        SetNoteOff(previous_note, 0)
    # construct the MIDI message
    if midichannel is None:
        msg = mido.Message('note_on', note=note, velocity=velocity)
    else:
        msg = mido.Message('note_on', note=note, velocity=velocity, channel=midichannel)
    # send the MIDI message
    previous_note = note
    outputport.send(msg)
    # schedule a timer to switch it off after the specified duration
    if duration_note != None:
        t = threading.Timer(duration_note, SetNoteOff, args=[note, 0])
        t.start()


def SetNoteOff(note, velocity):
    global previous_note
    if monophonic and previous_note != note:
        # do not switch off notes other than the previous one
        return
    # construct the MIDI message
    if midichannel is None:
        msg = mido.Message('note_off', note=note, velocity=velocity)
    else:
        msg = mido.Message('note_off', note=note, velocity=velocity, channel=midichannel)
    # send the MIDI message
    previous_note = None
    outputport.send(msg)


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

    if name == 'note':
        # note_on and note_off messages are dealt with in another function
        SetNoteOn(val, velocity_note)
        return
    elif name.startswith('note'):
        # note_on and note_off messages are dealt with in another function
        SetNoteOn(code, val)
        return

    monitor.info(name, code, val)

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
    outputport.send(msg)


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
        pubsub.subscribe(self.redischannel)     # this message contains the value of interest
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    monitor.debug(item['channel'], '=', item['data'])
                    # map the Redis values to MIDI values
                    val = float(item['data'])
                    # the scale and offset options are channel specific and can be changed on the fly
                    scale = patch.getfloat('scale', self.name, default=127)
                    offset = patch.getfloat('offset', self.name, default=0)
                    val = EEGsynth.rescale(val, slope=scale, offset=offset)
                    with lock:
                        sendMidi(self.name, self.code, val)


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, name
    global debug, mididevice, port, previous_note, UpdateVelocity, UpdateDuration, TriggerThread, trigger_name, trigger_code, code, trigger, this, thread, control_name, control_code, previous_val, SetNoteOff, SetNoteOn, duration_note, lock, midichannel, monitor, monophonic, offset_duration, offset_velocity, outputport, scale_duration, scale_velocity, sendMidi, velocity_note

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug       = patch.getint('general', 'debug')
    monophonic  = patch.getint('general', 'monophonic', default=1)
    midichannel = patch.getint('midi', 'channel')-1  # channel 1-16 get mapped to 0-15
    mididevice  = patch.getstring('midi', 'device')
    mididevice  = EEGsynth.trimquotes(mididevice)
    mididevice  = process.extractOne(mididevice, mido.get_output_names())[0] # select the closest match

    # values between 0 and 1 work well for the note duration
    scale_duration  = patch.getfloat('scale', 'duration', default=1)
    offset_duration = patch.getfloat('offset', 'duration', default=0)
    # values around 64 work well for the note velocity
    scale_velocity  = patch.getfloat('scale', 'velocity', default=1)
    offset_velocity = patch.getfloat('offset', 'velocity', default=0)

    # this is only for debugging, and to check which MIDI devices are accessible
    monitor.info('------ INPUT ------')
    for port in mido.get_input_names():
        monitor.info(port)
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

    previous_note = None
    velocity_note = None
    duration_note = None

    def UpdateVelocity():
        global velocity_note
        velocity_note = patch.getfloat('velocity', 'note', default=64)
        velocity_note = int(EEGsynth.rescale(velocity_note, slope=scale_velocity, offset=offset_velocity))

    def UpdateDuration():
        global duration_note
        duration_note = patch.getfloat('duration', 'note', default=None)
        if duration_note != None:
            duration_note = EEGsynth.rescale(duration_note, slope=scale_duration, offset=offset_duration)
            # some minimal time is needed for the duration
            duration_note = EEGsynth.limit(duration_note, 0.05, float('Inf'))

    # call them once at the start
    UpdateVelocity()
    UpdateDuration()

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

    # each of the Redis messages is mapped onto a different MIDI message
    trigger = []
    for name, code in zip(trigger_name, trigger_code):
        if config.has_option('trigger', name):
            # start the background thread that deals with this note
            this = TriggerThread(patch.getstring('trigger', name), name, code)
            trigger.append(this)
            monitor.debug(name, 'trigger configured')

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch
    global debug, mididevice, port, previous_note, UpdateVelocity, UpdateDuration, TriggerThread, trigger_name, trigger_code, code, trigger, this, thread, control_name, control_code, previous_val, SetNoteOff, SetNoteOn, duration_note, lock, midichannel, monitor, monophonic, offset_duration, offset_velocity, outputport, scale_duration, scale_velocity, sendMidi, velocity_note

    monitor.loop()
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
        with lock:
            sendMidi(name, code, val)


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r

    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTMIDI_UNBLOCK', 1)
    for thread in trigger:
        thread.join()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
