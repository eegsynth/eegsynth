#!/usr/bin/env python

# Inputmidi records MIDI data to Redis
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

# get the options from the configuration file
debug      = patch.getint('general','debug')
mididevice = patch.getstring('midi', 'device')
mididevice = EEGsynth.trimquotes(mididevice)

# the scale and offset are used to map MIDI values to Redis values
output_scale    = patch.getfloat('output', 'scale', default=1./127) # MIDI values are from 0 to 127
output_offset   = patch.getfloat('output', 'offset', default=0.)    # MIDI values are from 0 to 127

# this is only for debugging, check which MIDI devices are accessible
monitor.info('------ INPUT ------')
for port in mido.get_input_names():
  monitor.info(port)
monitor.info('-------------------------')

try:
    inputport = mido.open_input(mididevice)
    monitor.success('Connected to MIDI input')
except:
    raise RuntimeError("cannot connect to MIDI input")

while True:
    monitor.loop()
    time.sleep(patch.getfloat('general','delay'))

    for msg in inputport.iter_pending():
        monitor.debug(msg)

        if hasattr(msg, "control"):
            # prefix.control000=value
            key = "{}.control{:0>3d}".format(patch.getstring('output', 'prefix'), msg.control)
            val = msg.value
            # map the MIDI values to Redis values between 0 and 1
            val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
            patch.setvalue(key, val)

        elif hasattr(msg, "note"):
            # prefix.noteXXX=value
            key = "{}.note{:0>3d}".format(patch.getstring('output','prefix'), msg.note)
            val = msg.velocity
            patch.setvalue(key, val)
            key = "{}.note".format(patch.getstring('output','prefix'))
            val = msg.note
            patch.setvalue(key, val)
