#!/usr/bin/env python

# Outputcvgate outputs Redis data to our custom CV/Gate output device
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
import os
import redis
import serial
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

try:
    s = serial.Serial(patch.getstring('serial','device'), patch.getint('serial','baudrate'), timeout=3.0)
    if debug>0:
        print "Connected to serial port"
except:
    print "Error: cannot connect to serial port"
    exit()

while True:
    time.sleep(patch.getfloat('general','delay'))

    # loop over the control values
    for chanindx in range(1, 8):
        chanstr = "cv%d" % chanindx
        # this returns None when the channel is not present
        chanval = patch.getfloat('input', chanstr)

        if chanval==None:
            # the value is not present in Redis, skip it
            if debug>2:
                print chanstr, 'not available'
            continue

        # the scale and offset options are channel specific
    	scale  = patch.getfloat('scale', chanstr, default=4095)
    	offset = patch.getfloat('offset', chanstr, default=0)
        # apply the scale and offset
    	chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
        # ensure that it is within limits
        chanval = EEGsynth.limit(chanval, lo=0, hi=4095)
        chanval = int(chanval)

        s.write('*c%dv%04d#' % (chanindx, chanval))
        if debug>1:
            print chanstr, '=', chanval

    for chanindx in range(1, 8):
        chanstr = "gate%d" % chanindx
        chanval = patch.getfloat('input', chanstr)
        if chanval is None:
            continue

        # the value for the gate should be 0 or 1
        chanval = int(chanval>0)

        s.write('*g%dv%d#' % (chanindx, chanval))
        if debug>1:
            print chanstr, '=', chanval
