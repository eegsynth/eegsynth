#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'launchcontrol.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('------ INPUT ------')
for port in mido.get_input_names():
  print(port)
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

try:
    inputport  = mido.open_input(config.get('midi', 'device'))
    if debug>0:
        print "Connected to MIDI input"
except:
    print "Error: cannot connect to MIDI input"
    exit()

try:
    outputport  = mido.open_output(config.get('midi', 'device'))
    if debug>0:
        print "Connected to MIDI output"
except:
    print "Error: cannot connect to MIDI output"
    exit()

try:
    # channel 1-16 in the ini file should be mapped to 0-15
    midichannel = config.getint('midi', 'channel')-1
except:
    # this happens if it is not specified in the ini file
    # it will be determined on teh basis of the first incoming message
    midichannel = None

push     = [int(a) for a in config.get('button', 'push').split(",")]
toggle1  = [int(a) for a in config.get('button', 'toggle1').split(",")]
toggle2  = [int(a) for a in config.get('button', 'toggle2').split(",")]
toggle3  = [int(a) for a in config.get('button', 'toggle3').split(",")]
toggle4  = [int(a) for a in config.get('button', 'toggle4').split(",")]
note_list    = push+toggle1+toggle2+toggle3+toggle4 # concatenate all buttons
status_list  = [0] * len(note_list)

# these are the MIDI values for the LED color
Off         = 12
Red_Low     = 13
Red_Full    = 15
Amber_Low   = 29
Amber_Full  = 63
Yellow_Full = 62
Green_Low   = 28
Green_Full  = 60

def ledcolor(note,color):
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

state0change = {0:1, 1:0}
state0color  = {0:Off, 1:Red_Full}
state0value  = {0:0, 1:127}

state1change = {0:11, 11:12, 12:13, 13:0}
state1color  = {0:Off, 11:Red_Full}  # don't change color on 12,13
state1value  = {0:0, 11:127}         # don't send message on 12,13

state2change = {0:21, 21:22, 22:23, 23:24, 24:25, 25:0}
state2color  = {0:Off, 21:Red_Full, 23:Yellow_Full}         # don't change color on 22,24,25
state2value  = {0:Off, 21:int(127*1/2), 23:int(127*2/2)}    # don't send message on 22,24,25

state3change = {0:31, 31:32, 32:33, 33:34, 34:35, 35:36, 36:37, 37:0}
state3color  = {0:Off, 31:Red_Full, 33:Yellow_Full, 35:Green_Full}
state3value  = {0:Off, 31:int(127*1/3), 33:int(127*2/3), 35:int(127*3/3)}

state4change = {0:41, 41:42, 42:43, 43:44, 44:45, 45:46, 46:47, 47:48, 48:49, 49:0}
state4color  = {0:Off, 41:Red_Full, 43:Yellow_Full, 45:Green_Full, 47:Amber_Full}
state4value  = {0:Off, 41:int(127*1/4), 43:int(127*2/4), 45:int(127*3/4), 47:int(127*4/4)}

while True:
    time.sleep(config.getfloat('general','delay'))

    for msg in inputport.iter_pending():
        if midichannel is None:
            # specify the MIDI channel on the basis of the first incoming message
            midichannel = msg.channel

        if debug>0:
            print msg

        if hasattr(msg, "control"):
            # prefix.control000=value
            key = "{}.control{:0>3d}".format(config.get('output', 'prefix'), msg.control)
            val = msg.value
            r.set(key, val)

        elif hasattr(msg, "note"):
            # the default is not to send a message
            val = None
            # use an local variable as abbreviation in the subsequent code
            status = status_list[note_list.index(msg.note)]

            # change to the next state
            if   msg.note in toggle1:
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
            else:
                status = state0change[status]
                status_list[note_list.index(msg.note)] = status # remember the state
                if status in state0color.keys():
                    ledcolor(msg.note, state0color[status])
                if status in state0value.keys():
                    val = state0value[status]

            if debug>1:
                print status, val

            if not val is None:
                # prefix.noteXXX=value
                key = "{}.note{:0>3d}".format(config.get('output','prefix'), msg.note)
                r.set(key,val)          # send it as control value
                r.publish(key,val)      # send it as trigger
                # prefix.note=note
                key = "{}.note".format(config.get('output','prefix'))
                r.set(key,msg.note)          # send it as control value
                r.publish(key,msg.note)      # send it as trigger
