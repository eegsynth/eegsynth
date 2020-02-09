#!/usr/bin/env python

# This module interfaces with the Novation LaunchPad
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


def ledcolor(note,color):
    if not midichannel is None:
        outputport.send(mido.Message('note_on', note=int(note), velocity=color, channel=midichannel))


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
    global parser, args, config, r, response, patch
    global monitor, debug, push, toggle1, toggle2, toggle3, toggle4, slap, model, scale_note, scale_control, offset_note, offset_control, port, mididevice_input, mididevice_output, inputport, Off, Red_Full, Amber_Full, Yellow_Full, Green_Full, ledcolor, note_list, status_list, note, state0change, state0color, state0value, state1change, state1color, state1value, state2change, state2color, state2value, state3change, state3color, state3value, state4change, state4color, state4value, state5change, state5color, state5value, midichannel, outputport

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug       = patch.getint('general','debug')
    push        = patch.getint('button', 'push',    multiple=True)    # push-release button
    toggle1     = patch.getint('button', 'toggle1', multiple=True)    # on-off button
    toggle2     = patch.getint('button', 'toggle2', multiple=True)    # on1-on2-off button
    toggle3     = patch.getint('button', 'toggle3', multiple=True)    # on1-on2-on3-off button
    toggle4     = patch.getint('button', 'toggle4', multiple=True)    # on1-on2-on3-on4-off button
    slap        = patch.getint('button', 'slap',    multiple=True)    # slap button
    midichannel = patch.getint('midi', 'channel', default=None)
    model       = patch.getstring('midi', 'model', default='mk1')

    # the scale and offset are used to map MIDI values to Redis values
    scale_note     = patch.getfloat('scale', 'note', default=1./127)
    scale_control  = patch.getfloat('scale', 'control', default=1./127)
    offset_note    = patch.getfloat('offset', 'note', default=0)
    offset_control = patch.getfloat('offset', 'control', default=0)

    # this is only for debugging, check which MIDI devices are accessible
    monitor.info('------ INPUT ------')
    for port in mido.get_input_names():
        monitor.info(port)
    monitor.info('------ OUTPUT ------')
    for port in mido.get_output_names():
        monitor.info(port)
    monitor.info('-------------------------')

    # on windows the input and output are different, on unix they are the same
    # use "input/output" when specified, or otherwise use "device" for both
    try:
        mididevice_input = patch.getstring('midi', 'input')
        mididevice_input = EEGsynth.trimquotes(mididevice_input)
    except:
        mididevice_input = patch.getstring('midi', 'device') # fallback
        mididevice_input = EEGsynth.trimquotes(mididevice_input)
    try:
        mididevice_output = patch.getstring('midi', 'output')
        mididevice_output = EEGsynth.trimquotes(mididevice_output)
    except:
        mididevice_output = patch.getstring('midi', 'device') # fallback
        mididevice_output = EEGsynth.trimquotes(mididevice_output)

    mididevice_input  = process.extractOne(mididevice_input, mido.get_input_names())[0] # select the closest match
    mididevice_output = process.extractOne(mididevice_output, mido.get_output_names())[0] # select the closest match

    try:
        inputport = mido.open_input(mididevice_input)
        monitor.success('Connected to MIDI input')
    except:
        raise RuntimeError("cannot connect to MIDI input")

    try:
        outputport = mido.open_output(mididevice_output)
        monitor.success('Connected to MIDI output')
    except:
        raise RuntimeError("cannot connect to MIDI output")

    # channel 1-16 in the ini file should be mapped to 0-15
    if not midichannel is None:
        midichannel-=1
    monitor.update('midichannel', midichannel)

    monitor.info(model)

    # these are the MIDI values for the LED color
    if model == 'mk1':
        # the MK1 has a limited set of colors
        Off         = 12
        Red_Low     = 13
        Red_Full    = 15
        Amber_Low   = 29
        Amber_Full  = 63
        Yellow_Full = 62
        Green_Low   = 28
        Green_Full  = 60
    elif model == 'mk2':
        # the MK2 has a palette of 128 colors, here we try to mimic the limited set of colors from the MK1
        # the "low" colors are not defined, as they are not used further down
        Off         = 0
        Red_Full    = 72
        Amber_Full  = 124
        Yellow_Full = 16
        Green_Full  = 22

    # concatenate all buttons
    note_list    = push + toggle1 + toggle2 + toggle3 + toggle4 + slap # concatenate all buttons
    status_list  = [0] * len(note_list)

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
    state2color  = {0:Off, 21:Red_Full, 23:Yellow_Full}         # don't change color on 22,24,25
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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch
    global monitor, debug, push, toggle1, toggle2, toggle3, toggle4, slap, model, scale_note, scale_control, offset_note, offset_control, port, mididevice_input, mididevice_output, inputport, Off, Red_Full, Amber_Full, Yellow_Full, Green_Full, ledcolor, note_list, status_list, note, state0change, state0color, state0value, state1change, state1color, state1value, state2change, state2color, state2value, state3change, state3color, state3value, state4change, state4color, state4value, state5change, state5color, state5value, midichannel, outputport

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
            monitor.debug(msg)

        if hasattr(msg, "control"):
            # e.g. prefix.control000=value
            key = "{}.control{:0>3d}".format(patch.getstring('output', 'prefix'), msg.control)
            val = EEGsynth.rescale(msg.value, slope=scale_control, offset=offset_control)
            patch.setvalue(key, val)

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
                if status in list(state1color.keys()):
                    ledcolor(msg.note, state1color[status])
                if status in list(state1value.keys()):
                    val = state1value[status]
            elif msg.note in toggle2:
                status = state2change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in list(state2color.keys()):
                    ledcolor(msg.note, state2color[status])
                if status in list(state2value.keys()):
                    val = state2value[status]
            elif msg.note in toggle3:
                status = state3change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in list(state3color.keys()):
                    ledcolor(msg.note, state3color[status])
                if status in list(state3value.keys()):
                    val = state3value[status]
            elif msg.note in toggle4:
                status = state4change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in list(state4color.keys()):
                    ledcolor(msg.note, state4color[status])
                if status in list(state4value.keys()):
                    val = state4value[status]
            elif msg.note in slap:
                status = state5change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in list(state5color.keys()):
                    ledcolor(msg.note, state5color[status])
                if status in list(state5value.keys()):
                    val = state5value[status]
            else:
                status = state0change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in list(state0color.keys()):
                    ledcolor(msg.note, state0color[status])
                if status in list(state0value.keys()):
                    val = state0value[status]

            monitor.debug(status, val)

            if not val is None:
                # prefix.noteXXX=value
                key = "{}.note{:0>3d}".format(patch.getstring('output', 'prefix'), msg.note)
                val = EEGsynth.rescale(val, slope=scale_note, offset=offset_note)
                patch.setvalue(key, val)
                # prefix.note=note
                key = "{}.note".format(patch.getstring('output', 'prefix'))
                val = msg.note
                patch.setvalue(key, val)


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    pass


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
