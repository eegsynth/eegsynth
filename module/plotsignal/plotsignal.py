#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.fftpack
import redis
import argparse

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from scipy.signal import butter, lfilter
from scipy.interpolate import interp1d
# basis = '/Users/stephen/eegsynth/module/plotsignal/'

def butter_bandpass(lowcut, highcut, fs, order=9):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=9):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_lowpass(lowcut, fs, order=9):
    nyq = 0.5 * fs
    low = lowcut / nyq
    b, a = butter(order, low, btype='low')
    return b, a

def butter_lowpass_filter(data, lowcut, fs, order=9):
    b, a = butter_lowpass(lowcut, fs, order=order)
    y    = lfilter(b, a, data)
    return y

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = '../../eegsynth'

installed_folder = os.path.split(basis)[0]
# installed_folder = '/home/stephen/eegsynth/module/plotsignal'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
sys.path.insert(0,'../../lib/')

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
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

hdr_input = None
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
        hdr_input = ft_input.getHeader()
    time.sleep(0.2)

print "Data arrived"

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

#chan_nrs  = np.where(np.asarray([config.items('plot_channels')[i][1]=='on' for i in range(len(config.items('plot_channels')))]))[0]
#chanlist  = config.getfloat('arguments','channels',config, r, multiple=True)
chanlist = config.get('arguments','channels').split(",")
chanarray = np.array(chanlist)
for i in range(len(chanarray)):
    chanarray[i] = int(chanarray[i]) - 1 # since python using indexing from 0 instead of 1

chan_nrs = len(chanlist)

window    = config.getfloat('arguments','window')
window    = int(round(window*hdr_input.fSample))
clipsize  = config.getfloat('arguments','clipsize')
clipsize  = int(round(clipsize*hdr_input.fSample))
stepsize  = config.getfloat('arguments','stepsize')
lrate     = config.getfloat('arguments','learning_rate')

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth")
win.resize(1000,600)
win.setWindowTitle('EEGsynth')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
timeplot = [];
freqplot = [];
curve = [];
spect = [];
redleft = [];
redright = [];
blueleft = [];
blueright = [];
fft = [];
fft_old = [];
specmax = [];
specmin = [];
curvemax = [];

# Create panels (timecourse and spectrum) for each channel
for ichan in range(chan_nrs):
    channr = int(chanarray[ichan]) + 1
    timeplot.append(win.addPlot(title="%s%s" % ('Channel ',channr)))
    timeplot[ichan].setLabel('left',text = 'Amplitude')
    timeplot[ichan].setLabel('bottom',text = 'Time (s)')
    curve.append(timeplot[ichan].plot(pen='w'))
    freqplot.append(win.addPlot(title="%s%s" % ('Spectrum channel ',channr)))
    freqplot[ichan].setLabel('left',text = 'Power')
    freqplot[ichan].setLabel('bottom',text = 'Frequency (Hz)')

    spect.append(freqplot[ichan].plot(pen='w'))
    redleft.append(freqplot[ichan].plot(pen='r'))
    redright.append(freqplot[ichan].plot(pen='r'))
    blueleft.append(freqplot[ichan].plot(pen='b'))
    blueright.append(freqplot[ichan].plot(pen='b'))
    win.nextRow()

    # initialize as lists
    curvemax.append(0)
    specmin.append(0)
    specmax.append(0)
    fft.append(0)
    fft_old.append(0)

def update():
   global curvemax, specmax, specmin, fft_old, redfreq, redwidth, bluefreq, bluewidth, counter

   # get last data
   last_index = ft_input.getHeader().nSamples
   begsample = (last_index-window)
   endsample = (last_index-1)
   data = ft_input.getData([begsample,endsample])
   print "reading from sample %d to %d" % (begsample, endsample)

   # demean data before filtering to reduce edge artefacts and center timecourse
   data = data - np.sum(data,axis=0)/float(len(data))
   data = scipy.signal.detrend(data, axis=0)
   data = butter_bandpass_filter(data.T, 5, 40, 250, 9).T[clipsize:-clipsize]

   # spectral estimate looping over chan_nrs
   taper = np.hanning(len(data))

   for ichan in range(chan_nrs):

        channr = chanarray[ichan]
        fft[ichan] = abs(scipy.fft(taper*data[:,chanarray[ichan]])) * lrate + fft_old[ichan] * (1-lrate)
        fft_old[ichan] = fft[ichan]

        # freqency axis
        freqaxis = scipy.fftpack.fftfreq(len(data),1/hdr_input.fSample)

        # user-selected frequency band
        user_freqrange = config.get('arguments','freqrange').split("-")
        freqrange = np.greater(freqaxis,int(user_freqrange[0])) & np.less_equal(freqaxis,int(user_freqrange[1]))

        # time axis
        timeaxis = np.linspace(0,len(data)/hdr_input.fSample,len(data))

        # update timecourses
        curve[ichan].setData(timeaxis,data[:,channr])

        # update spectrum
        spect[ichan].setData(freqaxis[freqrange],fft[ichan][freqrange])

        # adapt scale to running mean of max
        curvemax[ichan] = float(curvemax[ichan])  * (1-lrate) + lrate * max(abs(data[:,ichan]))
        specmax[ichan] = float(specmax[ichan]) * (1-lrate) + lrate * max(fft[ichan][freqrange])
        specmin[ichan] = float(specmin[ichan]) * (1-lrate) + lrate * min(fft[ichan][freqrange])

        timeplot[ichan].setYRange(-curvemax[ichan], curvemax[ichan])
        freqplot[ichan].setYRange(specmin[ichan], specmax[ichan])

        # update plotted lines
        redfreq = EEGsynth.getfloat('input','redfreq', config, r, default=10)
        redfreq = redfreq * float(user_freqrange[1]) * EEGsynth.getfloat('scale','red', config, r, default=1/127)
        redwidth = EEGsynth.getfloat('input','redwidth', config, r, default=10)
        redwidth = redwidth * float(user_freqrange[1]) * EEGsynth.getfloat('scale','red', config, r, default=1/127)

        bluefreq = EEGsynth.getfloat('input','bluefreq', config, r, default=10)
        bluefreq = bluefreq * float(user_freqrange[1]) * EEGsynth.getfloat('scale','blue', config, r, default=1/127)
        bluewidth = EEGsynth.getfloat('input','bluewidth', config, r, default=10)
        bluewidth = bluewidth * float(user_freqrange[1]) * EEGsynth.getfloat('scale','blue', config, r, default=1/127)

        redleft[ichan].setData(x=[redfreq-redwidth,redfreq-redwidth],y=[specmin[ichan],specmax[ichan]])
        redright[ichan].setData(x=[redfreq+redwidth,redfreq+redwidth],y=[specmin[ichan],specmax[ichan]])
        blueleft[ichan].setData(x=[bluefreq-bluewidth,bluefreq-bluewidth],y=[specmin[ichan],specmax[ichan]])
        blueright[ichan].setData(x=[bluefreq+bluewidth,bluefreq+bluewidth],y=[specmin[ichan],specmax[ichan]])

   key = "%s.%s" % (config.get('output','prefix'), 'redband')
   r.set(key,[redfreq-redwidth,redfreq+redwidth])

   key = "%s.%s" % (config.get('output','prefix'), 'blueband')
   r.set(key,[bluefreq-bluewidth,bluefreq+bluewidth])

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(.01) # timeout
timer.start(stepsize)

# Wait until there is enough data
begsample = -1
while begsample<0:
    hdr_input = ft_input.getHeader()
    begsample = int(hdr_input.nSamples - window)

# Start
QtGui.QApplication.instance().exec_()
