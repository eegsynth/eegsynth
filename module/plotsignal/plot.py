#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from scipy.signal import butter, lfilter

basis = '/Users/stephen/eegsynth/module/plotsignal/'



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
    basis = '~/eegsynth'

installed_folder = os.path.split(basis)[0]
installed_folder = '/home/stephen/eegsynth/module/plotsignal'

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

if debug>1:
     print hdr_input
     print hdr_input.labels

# ensure that all input channels have a label
nInputs = hdr_input.nChannels
if len(hdr_input.labels)==0:
     for i in range(nInputs):
         hdr_input.labels.append('{}'.format(i+1))

 # get the input and output options
try:
     input_number, input_channel = map(list, zip(*config.items('channels')))

     # convert to integer and make the indices zero-offset
     input_number = [int(number)-1 for number in input_number]

     # update the labels with the ones specified in the ini file
     for number,channel in zip(input_number, input_channel):
         if number<nInputs:
             hdr_input.labels[number] = channel
except:
     pass

# get plot channels
plot_channels = np.where(np.asarray([config.items('plot_channels')[i][1]=='on' for i in range(len(config.items('plot_channels')))]))[0]

window    = config.getfloat('arguments','window')
window    = int(round(window*hdr_input.fSample))
# stepsize  = config.getfloat('arguments','stepsize')
# stepsize  = int(round(stepsize*hdr_input.fSample))
#
# if config.get('arguments','ylim').split(',')[1].replace(' ', '')[:-1] != 'inf' and config.get('arguments','ylim').split(',')[0].replace(' ', '')[2:] != 'inf':
#     ymin = float(config.get('arguments','ylim').split(',')[0].replace(' ', '')[1:])
#     ymax = float(config.get('arguments','ylim').split(',')[1].replace(' ', '')[:-1])
# else:
#     ymax=np.inf

begsample = -1
while begsample<0:
    # wait until there is enough data
    hdr_input = ft_input.getHeader()
    # jump to the end of the stream
    begsample = int(hdr_input.nSamples - window)
    endsample = int(hdr_input.nSamples - 1)

# initialize window with data
while endsample>hdr_input.nSamples-1:
    # wait until there is enough data
    time.sleep(config.getfloat('general', 'delay'))
    hdr_input = ft_input.getHeader()

# global data
# data = ft_input.getData([begsample, endsample])[:, plot_channels]




#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsWindow(title="Into the Mind of Berzelius")
win.resize(1000,600)
win.setWindowTitle('Into the Mind of Berzelius')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Channel 1")
curve1 = p1.plot(pen='w')
win.nextRow()

p2 = win.addPlot(title="Channel 2")
curve2 = p2.plot(pen='w')
# data = np.random.normal(size=(1,1000))
# app.processEvents()

client = FieldTrip.Client()
client.connect(hostname='127.0.0.1')

ptr = 0
curmax1 = 0
curmax2 = 0

def update():
   global curve1, curve2, data, p1, p2, client, plot_channels, curmax1, curmax2

   #plot_channels = np.arange(3)

   last_index = client.getHeader().nSamples
   data = client.getData([(last_index-window),(last_index-1)])[:,np.arange(2)]

   #process data
   #data = scipy.signal.detrend(data)
   data = data - np.sum(data,axis=0)/float(len(data))

   data = butter_bandpass_filter(data.T, 5, 40, 250, 9).T[100:-100]


   curve1.setData(data[:,0])
   curve2.setData(data[:,1])

   if max(abs(data[:,0])) > curmax1:
       curmax1 = curmax1 * .90 + .1 * max(abs(data[:,0]))
       p1.setYRange(-curmax1, curmax1)

   if max(abs(data[:,1])) > curmax2:
       curmax2 = curmax2 * .90 + .1 * max(abs(data[:,1]))
       p2.setYRange(-curmax2, curmax2)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(.0)
timer.start(20)

QtGui.QApplication.instance().exec_()

# create lpfilter
# lp_b, lp_a = scipy.signal.butter(3, 0.3)



#
# while True:
#
# #    if debug>1:
# #        print endsample
#
# #    while endsample>hdr_input.nSamples-1:
# #        # wait until there is enough data
#     time.sleep(.2)
# #        hdr_input = ft_input.getHeader()
# #
# #    data = ft_input.getData([begsample, endsample])[:, plot_channels]
#     data = np.random.normal(size=(1,1000))
#
#     curve.setData(data[0])
#     p6.show()
#     p6.update()
#     # app.processEvents()
#
#     # process data
#     #data = scipy.signal.detrend(data)
#     #data = data - sum(data)/float(len(data))
#     #data = scipy.signal.filtfilt(lp_b,lp_a,data,axis=0)
#
#     #plt.plot(data, linewidth=config.getfloat('arguments','linewidth'))
#     ##plt.plot(data)
#     #plt.draw()
#     #plt.show()
#     #plt.xlabel(config.get('arguments','xlabel')); plt.ylabel(config.get('arguments','ylabel'))
#     #if ymax!=np.inf:
#     #    plt.axis([0, len(data), ymin, ymax])
#     #plt.title(config.get('arguments', 'title'), fontsize=config.getfloat('arguments', 'fontsize'))
#     #plt.pause(config.getfloat('general', 'delay'))
#     #plt.pause(0.01)
#     #plt.hold(False)
#
#     # increment the counters for the next loop
#     # begsample += stepsize
#     # endsample += stepsize
