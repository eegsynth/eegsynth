#!/usr/bin/env python

# Sequencer acts as a basic timer and sequencer
#
# Sequencer is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import argparse
import math
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

# these scale and offset parameters are used to map Redis values to internal values
scale_pattern    = patch.getfloat('scale',  'pattern',   default=127) # internal MIDI values
scale_transpose  = patch.getfloat('scale',  'transpose', default=127) # internal MIDI values
scale_rate       = patch.getfloat('scale',  'rate',      default=127) # beats per minute
offset_pattern   = patch.getfloat('offset', 'pattern',   default=0)
offset_transpose = patch.getfloat('offset', 'transpose', default=0)
offset_rate      = patch.getfloat('offset', 'rate',      default=0)

# the output scale and offset are used to map the internal MIDI values to Redis values
output_scale  = patch.getfloat('output', 'scale', default=0.00787401574803149606)
output_offset = patch.getfloat('output', 'offset', default=0)

if debug>0:
    print 'scale_pattern    =', scale_pattern
    print 'scale_transpose  =', scale_transpose
    print 'scale_rate       =', scale_rate
    print 'offset_pattern   =', offset_pattern
    print 'offset_transpose =', offset_transpose
    print 'offset_rate      =', offset_rate

previous_pattern   = -1
previous_transpose = -1
previous_rate      = -1

# this is just to get started
sequence = '0'

try:
    while True:

        for note in sequence.split():
            # the note should be a value, not a string
            note = float(note)

            # the pattern should be an integer between 0 and 127
            pattern = patch.getfloat('control','pattern', default=0)
            pattern = EEGsynth.rescale(pattern, slope=scale_pattern, offset=offset_pattern)
            pattern = int(pattern)

            if pattern!=previous_pattern:
                if debug>0:
                    print 'pattern =', pattern
                previous_pattern = pattern
                # get the corresponding sequence
                try:
                    sequence = patch.getstring('sequence',"pattern{:d}".format(pattern))
                except:
                    sequence = '0'
                # immediately start playing the new sequence
                break

            # use a default transposition of 48
            transpose = patch.getfloat('control','transpose', default=48./127)
            transpose = EEGsynth.rescale(transpose, slope=scale_transpose, offset=offset_transpose)

            if transpose!=previous_transpose:
                if debug>0:
                    print 'transpose =',  transpose
                previous_transpose = transpose

            # use a default rate of 90 bpm
            rate = patch.getfloat('control','rate', default=90./127)
            rate = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)

            if rate!=previous_rate:
                if debug>0:
                    print 'rate =',  rate
                previous_rate = rate

            # assume that the rate value is between 0 and 127, map it exponentially from 60 to 600
            # it should not get too low, otherwise the code with the sleep below becomes unresponsive
            rate = 60. * math.exp(math.log(10) * rate/127)

            if debug>1:
                print '-----------------------'
                print 'pattern   =', pattern
                print 'rate      =', rate
                print 'transpose =', transpose
                print 'note      =', note

            key = "{}.note".format(patch.getstring('output','prefix'))
            val = note + transpose

            # map the internally used values to Redis values
            val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)

            if debug>0:
                print key, '=', note, note + transpose, val

            r.set(key, val)     # send it as control value
            r.publish(key, val) # send it as trigger

            time.sleep(60./rate)

except KeyboardInterrupt:
    try:
        print "Disabling last note"
        r.set(key,0)
        r.publish(key,0)
    except:
        pass
