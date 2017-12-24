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
import numpy as np
import os
import pyqtgraph as pg
import sys
import math
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
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

# this determines how much debugging information gets printed
debug = config.getint('general', 'debug')

try:
    r = redis.StrictRedis(host=config.get('redis',  'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

inputlist = config.get('input', 'channels').split(",")
input_nrs = int(len(inputlist))
stepsize = config.getfloat('arguments', 'stepsize')
historysize = int(config.getfloat('arguments', 'window') / stepsize)
learning_rate = config.getfloat('arguments', 'learning_rate')
secwindow = config.getfloat('arguments', 'window')

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth")
win.resize(1000, 600)
win.setWindowTitle('EEGsynth')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
inputhistory = np.ones((input_nrs, historysize))
calibhistory = np.ones((input_nrs, historysize))
inputplot = []
inputcurve = []
inputmincurve = []
inputmaxcurve = []
inputmincurveadd = []
inputmaxcurveadd = []
inputmin = np.ones((input_nrs, historysize))
inputmax = np.ones((input_nrs, historysize))
inputminadd = np.ones((input_nrs, historysize))
inputmaxadd = np.ones((input_nrs, historysize))
calibplot = []
calibcurve = []
attcurvemax = []
attcurvemin = []

# Create panel for each channel
for iplot in range(input_nrs):

    inputplot.append(win.addPlot(title="%s" % (inputlist[iplot])))
    inputplot[iplot].setLabel('bottom', text = 'Time (sec)')
    xax = inputplot[iplot].getAxis('left')
    xax.setStyle(showValues=False)

    attcurvemax.append(inputplot[iplot].plot(pen=[128, 128, 128]))
    attcurvemin.append(inputplot[iplot].plot(pen=[128, 128, 128]))
    inputcurve.append(inputplot[iplot].plot(pen='w'))
    inputmaxcurve.append(inputplot[iplot].plot(pen=[128, 0, 0]))
    inputmincurve.append(inputplot[iplot].plot(pen=[0, 128, 0]))
    inputmaxcurveadd.append(inputplot[iplot].plot(pen=[255, 0, 0]))
    inputmincurveadd.append(inputplot[iplot].plot(pen=[0, 255, 0]))

    calibplot.append(win.addPlot(title="%s%s" % (inputlist[iplot], '.calib')))
    calibplot[iplot].setLabel('left', text = 'Value')
    calibplot[iplot].setLabel('bottom', text = 'Time (sec)')
    calibplot[iplot].setYRange(0.0, 1.0)
    calibplot[iplot].setMouseEnabled(False, False)

    calibplot[iplot].showGrid(x=False, y=True, alpha=0.5)
    calibcurve.append(calibplot[iplot].plot(pen='w'))

    win.nextRow()

def update():

   learning_att = EEGsynth.getfloat('attenuation_history', 'value', config, r, default=63)
   learning_att = learning_att + EEGsynth.getfloat('attenuation_history', 'offset', config, r, default=0)
   learning_att = learning_att * EEGsynth.getfloat('attenuation_history', 'scaling', config, r, default=1)
   if learning_att > 1.0:
        learning_att = 1
   if learning_att < 0.0:
        learning_att = 0
   learning_att = 1 - learning_att

   gain_att = EEGsynth.getfloat('expansion', 'value', config, r, default=63)
   gain_att = gain_att + EEGsynth.getfloat('expansion', 'offset', config, r, default=0)
   gain_att = gain_att * EEGsynth.getfloat('expansion', 'scaling', config, r, default=1)
   if gain_att > 1.0:
        gain_att = 1
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
   for iplot in range(input_nrs):

        inputhistory[iplot, historysize-1] = r.get(inputlist[iplot])

        # determine max and min, with learning rate and attenuated history
        thistory = inputhistory[iplot, 0:historysize-2]
        tmed = np.mean(inputhistory[iplot, 0:historysize-2])

        thistory = (thistory-tmed) * np.linspace(learning_att, 1, len(thistory)) + tmed
        inputmax[iplot, historysize-1] = max(thistory) * learning_rate + inputmax[iplot, historysize-1] * (1-learning_rate)
        inputmin[iplot, historysize-1] = min(thistory) * learning_rate + inputmin[iplot, historysize-1] * (1-learning_rate)
        inputmaxadd[iplot, historysize-1] = inputmax[iplot, historysize-1] + (inputmax[iplot, historysize-1] - ((inputmax[iplot, historysize-1] + inputmin[iplot, historysize-1])/2)) * gain_att * 2
        inputminadd[iplot, historysize-1] = inputmin[iplot, historysize-1] - (inputmax[iplot, historysize-1] - ((inputmax[iplot, historysize-1] + inputmin[iplot, historysize-1])/2)) * gain_att * 2

        l = int(historysize * learning_att)
        attcurvemaxvalues = np.linspace(tmed, inputmax[iplot, historysize-1], l)
        attcurveminvalues = np.linspace(tmed, inputmin[iplot, historysize-1], l)

        # calibration, avoiding divide by zero
        if (inputmaxadd[iplot, historysize-1] - inputminadd[iplot, historysize-1]) > 0:
            calibhistory[iplot, historysize-1] = (inputhistory[iplot, historysize - 1] - inputminadd[iplot, historysize-1]) / (inputmaxadd[iplot, historysize-1] - inputminadd[iplot, historysize-1])
        else:
            calibhistory[iplot, historysize - 1] = 0.5


        # time axis
        timeaxis = np.linspace(-secwindow, 0, historysize)

        # update timecourses
        inputcurve[iplot].setData(timeaxis, inputhistory[iplot, :])
        inputmaxcurve[iplot].setData(timeaxis, inputmax[iplot, :])
        inputmincurve[iplot].setData(timeaxis, inputmin[iplot, :])
        inputmaxcurveadd[iplot].setData(timeaxis, inputmaxadd[iplot, :])
        inputmincurveadd[iplot].setData(timeaxis, inputminadd[iplot, :])

        attcurvemin[iplot].setData(timeaxis[historysize-l:historysize], attcurveminvalues)
        attcurvemax[iplot].setData(timeaxis[historysize-l:historysize], attcurvemaxvalues)

        calibcurve[iplot].setData(timeaxis, calibhistory[iplot, :])

        # output min/max and calibrated to redis, appended to input keys
        key = (inputlist[iplot] + '.min')
        r.set(key, inputminadd[iplot, historysize-1])
        key = (inputlist[iplot] + '.max')
        r.set(key, inputmaxadd[iplot, historysize-1])
        key = (inputlist[iplot] + '.calib')
        r.set(key, calibhistory[iplot, historysize-1])

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(.01) # timeout
timer.start(stepsize*1000)

# Start
QtGui.QApplication.instance().exec_()
