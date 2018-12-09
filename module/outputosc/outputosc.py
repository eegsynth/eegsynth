#!/usr/bin/env python

# OutputOSC sends redis data according to OSC protocol
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
import OSC          # see https://trac.v2.nl/wiki/pyOSC
import argparse
import os
import redis
import sys
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

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

try:
    s = OSC.OSCClient()
    s.connect((patch.getstring('osc','hostname'), patch.getint('osc','port')))
    if debug>0:
        print "Connected to OSC server"
except:
    print "Error: cannot connect to OSC server"
    exit()

# keys should be present in both the input and output section of the *.ini file
list_input  = config.items('input')
list_output = config.items('output')

list1 = [] # the key name that matches in the input and output section of the *.ini file
list2 = [] # the key name in Redis
list3 = [] # the key name in OSC
for i in range(len(list_input)):
    for j in range(len(list_output)):
        if list_input[i][0]==list_output[j][0]:
            list1.append(list_input[i][0])
            list2.append(list_input[i][1])
            list3.append(list_output[j][1])

while True:
    time.sleep(patch.getfloat('general', 'delay'))

    for key1,key2,key3 in zip(list1,list2,list3):

        val = patch.getfloat('input', key1, multiple=True )
        if any(item is None for item in val):
            # the control value is not present in redis, skip it
            continue
        else:
            val = [float(x) for x in val]

        # the scale and offset options are channel specific
        scale  = patch.getfloat('scale', key1, default=1)
        offset = patch.getfloat('offset', key1, default=0)
        # apply the scale and offset
        val = EEGsynth.rescale(val, slope=scale, offset=offset)

        if debug>1:
            print 'OSC message', key3, '=', val

        msg = OSC.OSCMessage(key3)
        msg.append(val)
        s.send(msg)
