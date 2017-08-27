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

config = ConfigParser.ConfigParser()

try:
    config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))
except:
    __file__ = 'plot.py'
    config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

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

chan_nrs  = np.where(np.asarray([config.items('plot_channels')[i][1]=='on' for i in range(len(config.items('plot_channels')))]))[0]
window    = config.getfloat('arguments','window')
window    = int(round(window*hdr_input.fSample))
clipsize  = config.getfloat('arguments','clipsize')
clipsize  = int(round(clipsize*hdr_input.fSample))
stepsize  = config.getfloat('arguments','stepsize')
lrate     = config.getfloat('arguments','learning_rate')

# initialize window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="Probing the Mind of Berzelius")
win.resize(1000,600)
win.setWindowTitle('Probing the Mind of Berzelius')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# draw window
p1 = win.addPlot(title="Channel 1")
p3 = win.addPlot(title="Spectrum channel 1")
win.nextRow()
p2 = win.addPlot(title="Channel 2")
p4 = win.addPlot(title="Spectrum channel 2")
curve1 = p1.plot(pen='w')
curve2 = p2.plot(pen='w')
spect1 = p3.plot(pen='w')
spect2 = p4.plot(pen='w')
p1.setLabel('left',text = 'Amplitude')
p2.setLabel('left',text = 'Amplitude')
p3.setLabel('left',text = 'Power')
p4.setLabel('left',text = 'Power')
p1.setLabel('bottom',text = 'Time (s)')
p2.setLabel('bottom',text = 'Time (s)')
p3.setLabel('bottom',text = 'Frequency (Hz)')
p4.setLabel('bottom',text = 'Frequency (Hz)')

# initialize global variables
curmax1  = 0
curmax2  = 0
specmax1 = 0
specmax2 = 0
specmin1 = 0
specmin2 = 0
fft1_old = 0
fft2_old = 0
counter  = 0

def update():
   global curmax1, curmax2, specmax1, specmax2, specmin1, specmin2, fft1_old, fft2_old

   # get last data
   last_index = ft_input.getHeader().nSamples
   data = ft_input.getData([(last_index-window),(last_index-1)])[:,chan_nrs]

   # demean data before filtering to reduce edge artefacts and center timecourse
   data = data - np.sum(data,axis=0)/float(len(data))
   data = scipy.signal.detrend(data, axis=0)
   data = butter_bandpass_filter(data.T, 5, 40, 250, 9).T[clipsize:-clipsize]

   # spectral estimate
   taper = np.hanning(len(data))
   fft1 = abs(scipy.fft(taper*data[:,0])) * lrate + fft1_old * (1-lrate)
   fft2 = abs(scipy.fft(taper*data[:,1])) * lrate + fft2_old * (1-lrate)
   fft1_old = fft1
   fft2_old = fft2

   # freqency axis
   freqaxis = scipy.fftpack.fftfreq(len(data),1/hdr_input.fSample)

   # selected frequency band
   user_freqrange = config.get('arguments','freqrange').split("-")
   freqrange = np.greater(freqaxis,int(user_freqrange[0])) & np.less_equal(freqaxis,int(user_freqrange[1]))

   # time axis
   timeaxis = np.linspace(0,len(data)/hdr_input.fSample,len(data))

   # update timecourses
   curve1.setData(timeaxis,data[:,0])
   curve2.setData(timeaxis,data[:,1])

   # update spectrum
   spect1.setData(freqaxis[freqrange],fft1[freqrange])
   spect2.setData(freqaxis[freqrange],fft2[freqrange])

   # adapt scale to running mean of max
   curmax1  = curmax1  * (1-lrate) + lrate * max(abs(data[:,0]))
   curmax2  = curmax2  * (1-lrate) + lrate * max(abs(data[:,1]))
   specmax1 = specmax1 * (1-lrate) + lrate * max(fft1[freqrange])
   specmax2 = specmax2 * (1-lrate) + lrate * max(fft2[freqrange])
   specmin1 = specmin1 * (1-lrate) + lrate * min(fft1[freqrange])
   specmin2 = specmin2 * (1-lrate) + lrate * min(fft2[freqrange])

   p1.setYRange(-curmax1, curmax1)
   p2.setYRange(-curmax2, curmax2)
   p3.setYRange(specmin1, specmax1)
   p4.setYRange(specmin2, specmax2)

# set timer
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(.01) # timeout
timer.start(stepsize)

# wait until there is enough data
begsample = -1
while begsample<0:
    hdr_input = ft_input.getHeader()
    begsample = int(hdr_input.nSamples - window)

# start
QtGui.QApplication.instance().exec_()
