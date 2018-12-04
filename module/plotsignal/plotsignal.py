#!/usr/bin/env python

# Plotsignal plots data from the FieldTrip buffer. Currently it also includes user-defined filtering
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
import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import argparse
import numpy as np
import os
import pyqtgraph as pg
import sys
import time
import signal
from scipy.fftpack import fft, fftfreq
from scipy.signal import butter, lfilter, detrend
from scipy.interpolate import interp1d

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
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout')


def butter_bandpass(lowcut, highcut, fs, order=9):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_lowpass(lowcut, fs, order=9):
    nyq = 0.5 * fs
    low = lowcut / nyq
    b, a = butter(order, low, btype='lowpass')
    return b, a


def butter_highpass(highcut, fs, order=9):
    nyq = 0.5 * fs
    high = highcut / nyq
    b, a = butter(order, high, btype='highpass')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=9):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def butter_lowpass_filter(data, lowcut, fs, order=9):
    b, a = butter_lowpass(lowcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def butter_highpass_filter(data, highcut, fs, order=9):
    b, a = butter_highpass(highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print "Waiting for data to arrive..."
    if (time.time() - start) > timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug > 0:
    print "Data arrived"
if debug > 1:
    print hdr_input
    print hdr_input.labels

# read variables from ini/redis
chanarray = patch.getint('arguments', 'channels', multiple=True)
chanarray = [chan - 1 for chan in chanarray] # since python using indexing from 0 instead of 1

chan_nrs    = len(chanarray)
window      = patch.getfloat('arguments', 'window')        # in seconds
window      = int(round(window * hdr_input.fSample))       # in samples
clipsize    = patch.getfloat('arguments', 'clipsize')      # in seconds
clipsize    = int(round(clipsize * hdr_input.fSample))     # in samples
stepsize    = patch.getfloat('arguments', 'stepsize')      # in seconds
winx        = patch.getfloat('display', 'xpos')
winy        = patch.getfloat('display', 'ypos')
winwidth    = patch.getfloat('display', 'width')
winheight   = patch.getfloat('display', 'height')
lrate       = patch.getfloat('arguments', 'learning_rate')

# lowpass, highpass and bandpass are optional, but mutually exclusive
filtorder = 9
if patch.hasitem('arguments', 'bandpass'):
    freqrange = patch.getfloat('arguments', 'bandpass', multiple=True)
elif patch.hasitem('arguments', 'lowpass'):
    freqrange = patch.getfloat('arguments', 'lowpass')
    freqrange = [np.nan, freqrange]
elif patch.hasitem('arguments', 'highpass'):
    freqrange = patch.getfloat('arguments', 'highpass')
    freqrange = [freqrange, np.nan]
else:
    freqrange = [np.nan, np.nan]

# initialize graphical window
app = QtGui.QApplication([])

win = pg.GraphicsWindow(title="EEGsynth plotsignal")
win.setWindowTitle('EEGsynth plotsignal')
win.setGeometry(winx, winy, winwidth, winheight)

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
timeplot = []
curve    = []
curvemax = []

# Create panels for each channel
for ichan in range(chan_nrs):
    channr = int(chanarray[ichan]) + 1

    timeplot.append(win.addPlot(title="%s%s" % ('Channel ', channr)))
    timeplot[ichan].setLabel('left', text='Amplitude')
    timeplot[ichan].setLabel('bottom', text='Time (s)')
    curve.append(timeplot[ichan].plot(pen='w'))
    win.nextRow()

    # initialize as list
    curvemax.append(0.0)


def update():
    global curvemax, counter

    # get the last available data
    last_index = ft_input.getHeader().nSamples
    begsample = (last_index - window)  # the clipsize will be removed from both sides after filtering
    endsample = (last_index - 1)

    if debug > 0:
        print "reading from sample %d to %d" % (begsample, endsample)

    data = ft_input.getData([begsample, endsample])

    # detrend data before filtering to reduce edge artefacts and to center timecourse
    if patch.getint('arguments', 'detrend', default=1):
        data = detrend(data, axis=0)

    # apply the user-defined filtering
    if not np.isnan(freqrange[0]) and not np.isnan(freqrange[1]):
        data = butter_bandpass_filter(data.T, freqrange[0], freqrange[1], int(hdr_input.fSample), filtorder).T
    elif not np.isnan(freqrange[1]):
        data = butter_lowpass_filter(data.T, freqrange[1], int(hdr_input.fSample), filtorder).T
    elif not np.isnan(freqrange[0]):
        data = butter_highpass_filter(data.T, freqrange[0], int(hdr_input.fSample), filtorder).T

    # remove the filter padding
    if clipsize > 0:
        data = data[clipsize:-clipsize]

    for ichan in range(chan_nrs):
        channr = int(chanarray[ichan])

        # time axis
        timeaxis = np.linspace(-window / hdr_input.fSample, 0, len(data))

        # update timecourses
        curve[ichan].setData(timeaxis, data[:, channr])

        # adapt the vertical scale to the running mean of max
        curvemax[ichan] = curvemax[ichan] * (1 - lrate) + lrate * max(abs(data[:, channr]))
        timeplot[ichan].setYRange(-curvemax[ichan], curvemax[ichan])


# keyboard interrupt handling
def sigint_handler(*args):
    QtGui.QApplication.quit()


signal.signal(signal.SIGINT, sigint_handler)

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(10)                       # timeout in milliseconds
timer.start(int(round(stepsize * 1000)))    # in milliseconds

# Wait until there is enough data
begsample = -1
while begsample < 0:
    hdr_input = ft_input.getHeader()
    begsample = int(hdr_input.nSamples - window)

# Start
QtGui.QApplication.instance().exec_()
