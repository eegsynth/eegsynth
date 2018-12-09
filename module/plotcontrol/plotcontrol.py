#!/usr/bin/env python

# Plotcontrol plots the (history of) control values
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

from pyqtgraph.Qt import QtGui, QtCore
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import argparse
import numpy as np
import os
import pyqtgraph as pg
import sys
import time
import signal
import math
from scipy.interpolate import interp1d
from scipy.signal import butter, lfilter

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

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

input_name, input_variable = zip(*config.items('input'))

# count total nr. of curves to be drawm
curve_nrs = 0
for i in range(len(input_name)):
    temp = input_variable[i].split(",")
    for ii in range(len(temp)):
        curve_nrs += 1

ylim_name, ylim_value = zip(*config.items('ylim'))
delay       = patch.getfloat('general', 'delay')
historysize = int(patch.getfloat('general', 'window') / delay)
secwindow   = patch.getfloat('general', 'window')
winx        = patch.getfloat('display', 'xpos')
winy        = patch.getfloat('display', 'ypos')
winwidth    = patch.getfloat('display', 'width')
winheight   = patch.getfloat('display', 'height')

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth plotcontrol")
win.setWindowTitle('EEGsynth plotcontrol')
win.setGeometry(winx, winy, winwidth, winheight)

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
inputhistory = np.ones((curve_nrs, historysize))
inputplot    = []
inputcurve   = []

# Create panels for each channel
for iplot in range(len(input_name)):

    inputplot.append(win.addPlot(title="%s" % (input_name[iplot])))
    inputplot[iplot].setLabel('bottom', text = 'Time (s)')
    inputplot[iplot].showGrid(x=False, y=True, alpha=0.5)

    try:
        index = ylim_name.index(input_name[iplot])
        temp = ylim_value[index].split(",")
        inputplot[iplot].setRange(yRange=(int(temp[0]), int(temp[1])))
        print "Setting Ylim according to user input"
    except:
        print "No Ylim giving, will let it flow"

    # if input_name == ylim_name
    # if any(input_name in s for s in ylim_name):

    temp = input_variable[iplot].split(",")
    for icurve in range(len(temp)):
        inputcurve.append(inputplot[iplot].plot(pen='w'))

    win.nextRow()

def update():

   # shift data to next sample
   # FIXME use np.roll instead of allocating new memory over and over again
   inputhistory[:, :-1] = inputhistory[:, 1:]

   # update with current data
   counter = 0
   for iplot in range(len(input_name)):

       input_variable_list = input_variable[iplot].split(",")

       for ivar in range(len(input_variable_list)):
            try:
                inputhistory[counter, historysize-1] = r.get(input_variable_list[ivar])
            except:
                inputhistory[counter, historysize-1] = np.nan

            # time axis
            timeaxis = np.linspace(-secwindow, 0, historysize)

            # update timecourses
            inputcurve[counter].setData(timeaxis, inputhistory[counter, :])
            counter += 1


# keyboard interrupt handling
def sigint_handler(*args):
    QtGui.QApplication.quit()


signal.signal(signal.SIGINT, sigint_handler)

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(10)            # timeout in milliseconds
timer.start(int(delay * 1000))   # in milliseconds

# Start
QtGui.QApplication.instance().exec_()
