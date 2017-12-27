#!/usr/bin/env python

# Outputcvgate outputs redis data to our custom CVgate output device
#
# Outputcvgate is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    s = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)
    if debug>0:
        print "Connected to serial port"
except:
    print "Error: cannot connect to serial port"
    exit()

while True:
    time.sleep(config.getfloat('general','delay'))

    for chanindx in range(1, 8):
        chanstr = "cv%d" % chanindx
        chanval = EEGsynth.getfloat('input', chanstr, config, r)
        if chanval is None:
            continue

        if EEGsynth.getint('compressor_expander', 'enable', config, r):
            # the compressor applies to all channels and must exist as float or redis key
            lo = EEGsynth.getfloat('compressor_expander', 'lo', config, r)
            hi = EEGsynth.getfloat('compressor_expander', 'hi', config, r)
            if lo is None or hi is None:
                if debug>1:
                    print "cannot apply compressor/expander"
            else:
                # apply the compressor/expander
                chanval = EEGsynth.compress(chanval, lo, hi)

    	scale  = EEGsynth.getfloat('scale', chanstr, config, r)
    	offset = EEGsynth.getfloat('offset', chanstr, config, r)
    	if debug>1:
    		print chanstr, chanval, scale, offset
    	chanval = EEGsynth.rescale(chanval, scale, offset)
        s.write('*c%dv%04d#' % (chanindx, chanval))

    for chanindx in range(1, 8):
        chanstr = "gate%d" % chanindx
        chanval = EEGsynth.getfloat('input', chanstr, config, r)
        if chanval is None:
            continue

        # the value for the gate should be 0 or 1
        chanval = int(chanval>0)
        if debug>1:
            print chanstr, chanval
        s.write('*g%dv%d#' % (chanindx, chanval))
