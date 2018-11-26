#!/usr/bin/env python

# This module interfaces with the Novation LaunchControl and LaunchControl XL
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
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
import mido
import os
import redis
import sys
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder, '../../lib'))
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
debug = patch.getint('general', 'debug')

# this is only for debugging, and check which MIDI devices are accessible
print('------ INPUT ------')
for port in mido.get_input_names():
  print(port)
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

# on windows the input and output are different, on unix they are the same
# use "input/output" when specified, or otherwise use "device" for both
try:
    mididevice_input = patch.getstring('midi', 'input')
except:
    mididevice_input = patch.getstring('midi', 'device') # fallback
try:
    mididevice_output = patch.getstring('midi', 'output')
except:
    mididevice_output = patch.getstring('midi', 'device') # fallback

print mididevice_input
print mididevice_output

try:
    inputport = mido.open_input(mididevice_input)
    if debug > 0:
        print "Connected to MIDI input"
except:
    print "Error: cannot connect to MIDI input"
    exit()

try:
    outputport = mido.open_output(mididevice_output)
    if debug > 0:
        print "Connected to MIDI output"
except:
    print "Error: cannot connect to MIDI output"
    exit()

try:
    # channel 1-16 in the ini file should be mapped to 0-15
    midichannel = patch.getint('midi', 'channel')-1
except:
    # this happens if it is not specified in the ini file
    # it will be determined on the basis of the first incoming message
    midichannel = None
print "midichannel = ", midichannel

push    = patch.getint('button', 'push',    multiple=True)      # push-release button
toggle1 = patch.getint('button', 'toggle1', multiple=True)      # on-off button
toggle2 = patch.getint('button', 'toggle2', multiple=True)      # on1-on2-off button
toggle3 = patch.getint('button', 'toggle3', multiple=True)      # on1-on2-on3-off button
toggle4 = patch.getint('button', 'toggle4', multiple=True)      # on1-on2-on3-on4-off button
slap    = patch.getint('button', 'slap',    multiple=True)      # slap button

# concatenate all buttons
note_list = push + toggle1 + toggle2 + toggle3 + toggle4 + slap
status_list = [0] * len(note_list)

# these are the MIDI values for the LED color
Off         = 12
Red_Low     = 13
Red_Full    = 15
Amber_Low   = 29
Amber_Full  = 63
Yellow_Full = 62
Green_Low   = 28
Green_Full  = 60

def ledcolor(note, color):
    if not midichannel is None:
    	outputport.send(mido.Message('note_on', note=int(note), velocity=color, channel=midichannel))

# ensure that all buttons and published messages start in the Off state
for note in note_list:
    ledcolor(note, Off)

# the button handling is implemented using an internal representation and state changes
# whenever the actual button is pressed or released

# push    button sequence P-R                   results in state change 0-1-0
# toggle1 button sequence P-R-P-R               results in state change 0-11-12-13-0
# toggle2 button sequence P-R-P-R-P-R           results in state change 0-21-22-23-24-25-0
# toggle3 button sequence P-R-P-R-P-R-P-R       results in state change 0-31-32-33-34-35-36-37-0
# toggle4 button sequence P-R-P-R-P-R-P-R-P-R   results in state change 0-41-42-43-44-45-46-47-48-49-0
# slap    button sequence P-R                   results in state change 0-51-0

state0change = {0:1, 1:0}
state0color  = {0:Off, 1:Red_Full}
state0value  = {0:0, 1:127}

state1change = {0:11, 11:12, 12:13, 13:0}
state1color  = {0:Off, 11:Red_Full}  # don't change color on 12,13
state1value  = {0:0, 11:127}         # don't send message on 12,13

state2change = {0:21, 21:22, 22:23, 23:24, 24:25, 25:0}
state2color  = {0:Off, 21:Red_Full, 23:Yellow_Full}       # don't change color on 22,24,25
state2value  = {0:0, 21:int(127*1/2), 23:int(127*2/2)}    # don't send message on 22,24,25

state3change = {0:31, 31:32, 32:33, 33:34, 34:35, 35:36, 36:37, 37:0}
state3color  = {0:Off, 31:Red_Full, 33:Yellow_Full, 35:Green_Full}
state3value  = {0:0, 31:int(127*1/3), 33:int(127*2/3), 35:int(127*3/3)}

state4change = {0:41, 41:42, 42:43, 43:44, 44:45, 45:46, 46:47, 47:48, 48:49, 49:0}
state4color  = {0:Off, 41:Red_Full, 43:Yellow_Full, 45:Green_Full, 47:Amber_Full}
state4value  = {0:0, 41:int(127*1/4), 43:int(127*2/4), 45:int(127*3/4), 47:int(127*4/4)}

state5change = {0:1, 1:0}
state5color  = {0:Off, 1:Amber_Full}
state5value  = {0:None, 1:127}  # don't send message on button release

# it is preferred to use floating point control values between 0 and 1 in Redis
scale_note     = patch.getfloat('scale', 'note', default=0.00787401574803149606)
scale_control  = patch.getfloat('scale', 'control', default=0.00787401574803149606)
offset_note    = patch.getfloat('offset', 'note', default=0)
offset_control = patch.getfloat('offset', 'control', default=0)

while True:
    time.sleep(patch.getfloat('general', 'delay'))

    for msg in inputport.iter_pending():
        if midichannel is None:
            try:
                # specify the MIDI channel on the basis of the first incoming message
                midichannel = int(msg.channel)
            except:
                pass

        if debug>1 and msg.type!='clock':
            print msg

        if hasattr(msg, "control"):
            # e.g. prefix.control000=value
            key = "{}.control{:0>3d}".format(patch.getstring('output', 'prefix'), msg.control)
            val = EEGsynth.rescale(msg.value, slope=scale_control, offset=offset_control)
            patch.setvalue(key, val, debug=debug)

        elif hasattr(msg, "note"):
            # the default is not to send a message
            val = None
            # use an local variable as abbreviation in the subsequent code
            if msg.note not in note_list:
                # this note/button was not specified in the ini file, add it
                note_list = note_list+[msg.note]
                status_list = status_list+[0]
            # get the remembered status for this note/button
            status = status_list[note_list.index(msg.note)]

            # change to the next state
            if msg.note in toggle1:
                status = state1change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state1color.keys():
                    ledcolor(msg.note, state1color[status])
                if status in state1value.keys():
                    val = state1value[status]
            elif msg.note in toggle2:
                status = state2change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state2color.keys():
                    ledcolor(msg.note, state2color[status])
                if status in state2value.keys():
                    val = state2value[status]
            elif msg.note in toggle3:
                status = state3change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state3color.keys():
                    ledcolor(msg.note, state3color[status])
                if status in state3value.keys():
                    val = state3value[status]
            elif msg.note in toggle4:
                status = state4change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state4color.keys():
                    ledcolor(msg.note, state4color[status])
                if status in state4value.keys():
                    val = state4value[status]
            elif msg.note in slap:
                status = state5change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state5color.keys():
                    ledcolor(msg.note, state5color[status])
                if status in state5value.keys():
                    val = state5value[status]
            else:
                status = state0change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state0color.keys():
                    ledcolor(msg.note, state0color[status])
                if status in state0value.keys():
                    val = state0value[status]

            if debug > 1:
                print status, val

            if not val is None:
                # prefix.noteXXX=value
                key = "{}.note{:0>3d}".format(patch.getstring('output', 'prefix'), msg.note)
                val = EEGsynth.rescale(val, slope=scale_note, offset=offset_note)
                patch.setvalue(key, val, debug=debug)

                # prefix.note=note
                key = "{}.note".format(patch.getstring('output', 'prefix'))
                val = msg.note
                patch.setvalue(key, val, debug=debug)
