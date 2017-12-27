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

# assume that the control values are between 0 and 1
scale_pattern   = patch.getfloat('scale', 'pattern',   default=127) # MIDI values
scale_transpose = patch.getfloat('scale', 'transpose', default=127) # MIDI values
scale_rate      = patch.getfloat('scale', 'rate',      default=127) # beats per minute

offset_pattern   = patch.getfloat('offset', 'pattern',   default=0)
offset_transpose = patch.getfloat('offset', 'transpose', default=0)
offset_rate      = patch.getfloat('offset', 'rate',      default=0)

if debug>0:
    print 'scale_pattern    =', scale_pattern
    print 'scale_transpose  =', scale_transpose
    print 'scale_rate       =', scale_rate
    print 'offset_pattern   =', offset_pattern
    print 'offset_transpose =', offset_transpose
    print 'offset_rate      =', offset_rate

# the pattern should be an integer between 0 and 127
pattern = patch.getfloat('control','pattern', default=0)
pattern = EEGsynth.rescale(pattern, slope=scale_pattern, offset=offset_pattern)
pattern = int(pattern)
previous = pattern

try:
    sequence = patch.getstring('sequence',"pattern{:d}".format(pattern))
except:
    sequence = '0'

if debug>0:
    print 'pattern  =', pattern
    print 'sequence =', sequence

try:
    while True:

        for note in sequence.split():
            # the note should be an integer between 0 and 127
            note = int(note)

            # the pattern should be an integer between 0 and 127
            pattern = patch.getfloat('control','pattern', default=0)
            pattern = EEGsynth.rescale(pattern, slope=scale_pattern, offset=offset_pattern)
            pattern = int(pattern)

            if pattern!=previous:
                # get the corresponding sequence
                try:
                    sequence = patch.getstring('sequence',"pattern{:d}".format(pattern))
                except:
                    sequence = '0'

                # immediately start playing the new sequence
                previous = pattern
                print "switching to pattern", pattern
                break

            # use a default transposition of 48
            transpose = patch.getfloat('control','transpose', default=48./127)
            transpose = EEGsynth.rescale(transpose, slope=scale_transpose, offset=offset_transpose)

            # use a default rate of 90 bpm
            rate = patch.getfloat('control','rate', default=90./127)
            rate = EEGsynth.rescale(rate, slope=scale_rate, offset=offset_rate)

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

            if debug>0:
                print 'sending', key, 'with value', val

            r.set(key,val)      # send it as control value: prefix.channel000.note=note
            r.publish(key,val)  # send it as trigger: prefix.channel000.note=note

            time.sleep(60./rate)

except KeyboardInterrupt:
    try:
        print "Disabling last note"
        r.set(key,0)
        r.publish(key,0)
    except:
        pass
