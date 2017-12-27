#!/usr/bin/env python

# Normalizecontrol normalizes control values according to it's history. Specifically, it uses an adaptive max and min
# between which it divides the current value. The scaling can be adjusted to avoid clipping beyond 0-1.
#
# Normalizecontrol is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

from pyqtgraph.Qt import QtGui, QtCore
from scipy.interpolate import interp1d
from scipy.signal import butter, lfilter
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import argparse
import numpy as np
import os
import pyqtgraph as pg
import sys
import math
import time
import signal

def signal_handler(signal, frame):
    print("\nBye, bye!")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth
import FieldTrip

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

# read configuration settings
inputlist       = patch.getstring('input', 'channels').split(',')
input_nrs       = int(len(inputlist))
stepsize        = patch.getfloat('general', 'stepsize')
historysize     = int(patch.getfloat('general', 'window') / stepsize)
learning_rate   = patch.getfloat('general', 'learning_rate')
secwindow       = patch.getfloat('general', 'window')
outputminmax    = patch.getint('general', 'outputminmax')

# Initialize variables
inputhistory    = np.ones((input_nrs, historysize))
calibhistory    = np.ones((input_nrs, historysize))
inputmin        = np.ones((input_nrs, historysize))
inputmax        = np.ones((input_nrs, historysize))
inputminadd     = np.ones((input_nrs, historysize))
inputmaxadd     = np.ones((input_nrs, historysize))

while True:
   time.sleep(patch.getfloat('general', 'delay'))

   gain_att = patch.getfloat('attenuation', 'value', default=0.5)
   gain_att = gain_att + patch.getfloat('attenuation', 'offset', default=0)
   gain_att = gain_att * patch.getfloat('attenuation', 'scale', default=1)
   if gain_att < 0.0:
        gain_att = 0

   # shift data to next sample
   inputhistory[:, :-1] = inputhistory[:, 1:]
   inputmax[:, :-1] = inputmax[:, 1:]
   inputmin[:, :-1] = inputmin[:, 1:]
   inputmaxadd[:, :-1] = inputmaxadd[:, 1:]
   inputminadd[:, :-1] = inputminadd[:, 1:]
   calibhistory[:, :-1] = calibhistory[:, 1:]

   # update with current data
   for iinput in range(input_nrs):

        inputhistory[iinput, historysize-1] = r.get(inputlist[iinput])

        # determine max and min, with learning rate and attenuated history
        thistory = inputhistory[iinput, 0:historysize-2]
        tmed = np.mean(inputhistory[iinput, 0:historysize-2])

        thistory = (thistory-tmed) * np.linspace(0, 1, len(thistory)) + tmed
        inputmax[iinput, historysize-1] = max(thistory) * learning_rate + inputmax[iinput, historysize-1] * (1-learning_rate)
        inputmin[iinput, historysize-1] = min(thistory) * learning_rate + inputmin[iinput, historysize-1] * (1-learning_rate)
        inputmaxadd[iinput, historysize-1] = inputmax[iinput, historysize-1] + (inputmax[iinput, historysize-1] - ((inputmax[iinput, historysize-1] + inputmin[iinput, historysize-1])/2)) * gain_att * 2
        inputminadd[iinput, historysize-1] = inputmin[iinput, historysize-1] - (inputmax[iinput, historysize-1] - ((inputmax[iinput, historysize-1] + inputmin[iinput, historysize-1])/2)) * gain_att * 2

        # calibration, avoiding divide by zero
        if (inputmaxadd[iinput, historysize-1] - inputminadd[iinput, historysize-1]) > 0:
            calibhistory[iinput, historysize-1] = (inputhistory[iinput, historysize - 1] - inputminadd[iinput, historysize-1]) / (inputmaxadd[iinput, historysize-1] - inputminadd[iinput, historysize-1])
        else:
            calibhistory[iinput, historysize - 1] = 0.5

        # time axis
        timeaxis = np.linspace(-secwindow, 0, historysize)

        # output min/max to redis, appended to input keys
        if outputminmax == 1:
            key = (inputlist[iinput] + '.min')
            r.set(key, inputminadd[iinput, historysize-1])
            key = (inputlist[iinput] + '.max')
            r.set(key, inputmaxadd[iinput, historysize-1])

        # output min/max to redis, appended to input keys
        key = (inputlist[iinput] + '.norm')
        r.set(key, calibhistory[iinput, historysize-1])
