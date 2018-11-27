#!/usr/bin/env python

# Inputmidi records MIDI data to Redis
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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# this is only for debugging
print('------ INPUT ------')
for port in mido.get_input_names():
  print(port)
print('-------------------------')

# the scale and offset are used to map MIDI values to Redis values
scale  = patch.getfloat('output', 'scale', default=127)
offset = patch.getfloat('output', 'offset', default=0)

try:
    inputport  = mido.open_input(patch.getstring('midi', 'device'))
    if debug>0:
        print "Connected to MIDI input"
except:
    print "Error: cannot connect to MIDI input"
    exit()

while True:
    time.sleep(patch.getfloat('general','delay'))

    for msg in inputport.iter_pending():

        if debug>1:
            print msg

        if hasattr(msg, "control"):
            # prefix.control000=value
            key = "{}.control{:0>3d}".format(patch.getstring('output', 'prefix'), msg.control)
            val = msg.value
            # map the MIDI values to Redis values between 0 and 1
            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            patch.setvalue(key, val, debug=debug)

        elif hasattr(msg, "note"):
            # prefix.noteXXX=value
            key = "{}.note{:0>3d}".format(patch.getstring('output','prefix'), msg.note)
            val = msg.velocity
            patch.setvalue(key, val, debug=debug)
            key = "{}.note".format(patch.getstring('output','prefix'))
            val = msg.note
            patch.setvalue(key, val, debug=debug)
