#!/usr/bin/env python

# Plotcontrol plots the (history of) control signals, and adds an adaptive
# min and max for subsequent scaling using e.g. the postprocessing module
#
# Plotcontrol is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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
# import matplotlib.pyplot as plt
import numpy as np
import os
import pyqtgraph as pg
import sys
import time
# from scipy.signal import butter, lfilter, detrend
# from scipy.interpolate import interp1d
# from scipy.fftpack import fft, fftfreq

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
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

inputlist       = config.get('input','channels').split(",")
input_nrs       = int(len(inputlist))
stepsize        = config.getfloat('arguments','stepsize')
historysize     = int(config.getfloat('arguments','window') / stepsize)
learning_rate   = config.getfloat('arguments','learning_rate')
learning_att    = config.getfloat('arguments','learning_att')
secwindow       = config.getfloat('arguments','window')

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth")
win.resize(1000,600)
win.setWindowTitle('EEGsynth')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
history = np.ones((input_nrs,historysize))
history_max = np.ones(input_nrs)
history_min = np.zeros(input_nrs)
inputplot = []
inputcurve = []
inputmincurve = []
inputmaxcurve = []
inputmin = np.ones((input_nrs,historysize))
inputmax = np.ones((input_nrs,historysize))

# Create panels (timecourse and spectrum) for each channel
for iplot in range(input_nrs):
    inputplot.append(win.addPlot(title="%s" % (inputlist[iplot])))
    inputplot[iplot].setLabel('left',text = 'Value')
    inputplot[iplot].setLabel('bottom',text = 'Time (sec)')

    inputcurve.append(inputplot[iplot].plot(pen='w'))
    inputmaxcurve.append(inputplot[iplot].plot(pen='r'))
    inputmincurve.append(inputplot[iplot].plot(pen='g'))

    win.nextRow()

def update():
   # global input_nrs

   # shift data to next sample
   history[:,:-1] = history[:,1:]
   inputmax[:,:-1] = inputmax[:,1:]
   inputmin[:,:-1] = inputmin[:,1:]

   # update with current data
   for iplot in range(input_nrs):

        history[iplot,historysize-1] = r.get(inputlist[iplot])

        # determine max and min, with learning rate and attenuated history
        thistory = history[iplot,0:historysize-2]
        tmed = np.median(thistory)
        thistory = (thistory-tmed) * np.linspace(learning_att,1,len(thistory)) + tmed
        inputmax[iplot,historysize-1] = max(thistory) * learning_rate + inputmax[iplot,historysize-1] * (1-learning_rate)
        inputmin[iplot,historysize-1] = min(thistory) * learning_rate + inputmin[iplot,historysize-1] * (1-learning_rate)

        # time axis
        timeaxis = np.linspace(-secwindow,0,historysize)

        # update timecourses
        inputcurve[iplot].setData(timeaxis,history[iplot,:])
        inputmaxcurve[iplot].setData(timeaxis,inputmax[iplot,:])
        inputmincurve[iplot].setData(timeaxis,inputmin[iplot,:])

        # output min/max to redis, appended to input keys
        key = (inputlist[iplot] + '.min')
        r.set(key,inputmin[iplot,historysize-1])
        key = (inputlist[iplot] + '.max')
        r.set(key,inputmax[iplot,historysize-1])

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(.01) # timeout
timer.start(stepsize*1000)

# Start
QtGui.QApplication.instance().exec_()
