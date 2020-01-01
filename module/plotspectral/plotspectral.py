#!/usr/bin/env python

# Plotfreq plots spectral data from the buffer and allows interactive selection
# of frequency bands for further processing
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2019 EEGsynth project
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
import configparser
import redis
import argparse
import numpy as np
import os
import pyqtgraph as pg
import sys
import time
import signal
from scipy.fftpack import fft, fftfreq
from scipy.signal import butter, lfilter, detrend, filtfilt, decimate
from scipy.interpolate import interp1d

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug = patch.getint('general', 'debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip', 'timeout', default=30)


def notch(f0, fs, Q=30):
    # Q = Quality factor
    w0 = f0 / (fs / 2)  # Normalized Frequency
    b, a = iirnotch(w0, Q)
    return b, a


def notch_filter(dat, f0, fs, Q=30):
    b, a = notch(f0, fs, Q=Q)
    y = lfilter(b, a, dat)
    return y


try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print("Connected to input FieldTrip buffer")
except:
    raise RuntimeError("cannot connect to input FieldTrip buffer")

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print("Waiting for data to arrive...")
    if (time.time() - start) > timeout:
        print("Error: timeout while waiting for data")
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.1)

if debug > 0:
    print("Data arrived")
if debug > 1:
    print(hdr_input)
    print(hdr_input.labels)

# read variables from ini/redis
chanarray = patch.getint('arguments', 'channels', multiple=True)
chanarray = [chan - 1 for chan in chanarray] # since python starts counting at 0

numchannel  = len(chanarray)
window      = patch.getfloat('arguments', 'window')         # in seconds
stepsize    = patch.getfloat('arguments', 'stepsize')       # in seconds
historysize = patch.getfloat('arguments', 'historysize')    # in seconds
lrate       = patch.getfloat('arguments', 'learning_rate', default=0.2)
scale_red   = patch.getfloat('scale', 'red')
scale_blue  = patch.getfloat('scale', 'blue')
offset_red  = patch.getfloat('offset', 'red')
offset_blue = patch.getfloat('offset', 'blue')
winx        = patch.getfloat('display', 'xpos')
winy        = patch.getfloat('display', 'ypos')
winwidth    = patch.getfloat('display', 'width')
winheight   = patch.getfloat('display', 'height')
prefix      = patch.getstring('output', 'prefix')

window      = int(round(window * hdr_input.fSample))        # in samples
numhistory  = int(historysize / stepsize)                   # number of observations in the history
freqaxis    = fftfreq(window, 1. / hdr_input.fSample)
history     = np.empty((numchannel, freqaxis.shape[0], numhistory)) * np.nan

# ideally it should be possible to change these on the fly
showred     = patch.getint('input', 'showred', default=1)
showblue    = patch.getint('input', 'showblue', default=1)

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth plotspectral")
win.setWindowTitle('EEGsynth plotspectral')
win.setGeometry(winx, winy, winwidth, winheight)

# initialize graphical elements
text_redleft        = pg.TextItem("", anchor=( 1,  0), color='r')
text_redright       = pg.TextItem("", anchor=( 0,  0), color='r')
text_blueleft       = pg.TextItem("", anchor=( 1, -1), color='b')
text_blueright      = pg.TextItem("", anchor=( 0, -1), color='b')
text_redleft_hist   = pg.TextItem("", anchor=( 1,  0), color='r')
text_redright_hist  = pg.TextItem("", anchor=( 0,  0), color='r')
text_blueleft_hist  = pg.TextItem("", anchor=( 1, -1), color='b')
text_blueright_hist = pg.TextItem("", anchor=( 0, -1), color='b')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Initialize variables
freqplot_curr   = []
freqplot_hist   = []
spect_curr      = []
spect_hist      = []
redleft_curr    = []
redright_curr   = []
blueleft_curr   = []
blueright_curr  = []
redleft_hist    = []
redright_hist   = []
blueleft_hist   = []
blueright_hist  = []
fft_curr        = []
fft_hist        = []
specmax_curr    = []
specmin_curr    = []
specmax_hist    = []
specmin_hist    = []

# Create panels for each channel
for ichan in range(numchannel):
    channr = int(chanarray[ichan]) + 1

    freqplot_curr.append(win.addPlot(title="%s%s" % ('Spectrum channel ', channr)))
    freqplot_curr[ichan].setLabel('left', text='Power')
    freqplot_curr[ichan].setLabel('bottom', text='Frequency (Hz)')

    spect_curr.append(freqplot_curr[ichan].plot(pen='w'))
    redleft_curr.append(freqplot_curr[ichan].plot(pen='r'))
    redright_curr.append(freqplot_curr[ichan].plot(pen='r'))
    blueleft_curr.append(freqplot_curr[ichan].plot(pen='b'))
    blueright_curr.append(freqplot_curr[ichan].plot(pen='b'))

    freqplot_hist.append(win.addPlot(title="%s%s%s%s%s" % ('Averaged spectrum channel ', channr, ' (', historysize, 's)')))
    freqplot_hist[ichan].setLabel('left', text='Power')
    freqplot_hist[ichan].setLabel('bottom', text='Frequency (Hz)')

    spect_hist.append(freqplot_hist[ichan].plot(pen='w'))
    redleft_hist.append(freqplot_hist[ichan].plot(pen='r'))
    redright_hist.append(freqplot_hist[ichan].plot(pen='r'))
    blueleft_hist.append(freqplot_hist[ichan].plot(pen='b'))
    blueright_hist.append(freqplot_hist[ichan].plot(pen='b'))
    win.nextRow()

    # initialize as lists
    specmin_curr.append(None)
    specmax_curr.append(None)
    specmin_hist.append(None)
    specmax_hist.append(None)
    fft_curr.append(None)
    fft_hist.append(None)

# print frequency at lines
freqplot_curr[0].addItem(text_redleft)
freqplot_curr[0].addItem(text_redright)
freqplot_curr[0].addItem(text_blueleft)
freqplot_curr[0].addItem(text_blueright)
freqplot_hist[0].addItem(text_redleft_hist)
freqplot_hist[0].addItem(text_redright_hist)
freqplot_hist[0].addItem(text_blueleft_hist)
freqplot_hist[0].addItem(text_blueright_hist)


def update():
    global specmax_curr, specmin_curr, specmax_hist, specmin_hist, fft_hist, redfreq, redwidth, bluefreq, bluewidth, counter, history

    # get last dat
    last_index = ft_input.getHeader().nSamples
    begsample  = (last_index - window)
    endsample  = (last_index - 1)
    dat = ft_input.getData([begsample, endsample]).astype(np.double)

    if debug>0:
        print("reading from sample %d to %d" % (begsample, endsample))

    # demean and detrend the data before filtering to reduce edge artefacts and center timecourse
    dat = detrend(dat, axis=0)

    # taper the data
    taper = np.hanning(len(dat))
    dat = dat * taper[:, np.newaxis]

    # shift the data  to next sample
    history = np.roll(history, 1, axis=2)

    for ichan in range(numchannel):
        channr = int(chanarray[ichan])

        # estimate the absolute FFT amplitude at the current moment
        fft_curr[ichan] = abs(fft(dat[:, channr]))

        # update FFT history with the current estimate
        history[ichan, :, numhistory - 1] = fft_curr[ichan]
        fft_hist = np.nanmean(history, axis=2)

        # user-selected frequency band
        arguments_freqrange = patch.getfloat('arguments', 'freqrange', multiple=True)
        freqrange = np.greater(freqaxis, arguments_freqrange[0]) & np.less_equal(freqaxis, arguments_freqrange[1])

        # adapt the vertical scale to the running mean of the min/max
        if specmax_curr[ichan]==None:
            specmax_curr[ichan] = max(fft_curr[ichan][freqrange])
            specmin_curr[ichan] = min(fft_curr[ichan][freqrange])
            specmax_hist[ichan] = max(fft_hist[ichan][freqrange])
            specmin_hist[ichan] = min(fft_hist[ichan][freqrange])
        else:
            specmax_curr[ichan] = (1 - lrate) * float(specmax_curr[ichan]) + lrate * max(fft_curr[ichan][freqrange])
            specmin_curr[ichan] = (1 - lrate) * float(specmin_curr[ichan]) + lrate * min(fft_curr[ichan][freqrange])
            specmax_hist[ichan] = (1 - lrate) * float(specmax_hist[ichan]) + lrate * max(fft_hist[ichan][freqrange])
            specmin_hist[ichan] = (1 - lrate) * float(specmin_hist[ichan]) + lrate * min(fft_hist[ichan][freqrange])

        freqplot_curr[ichan].setXRange(arguments_freqrange[0], arguments_freqrange[1])
        freqplot_hist[ichan].setXRange(arguments_freqrange[0], arguments_freqrange[1])
        freqplot_curr[ichan].setYRange(specmin_curr[ichan], specmax_curr[ichan])
        freqplot_hist[ichan].setYRange(specmin_hist[ichan], specmax_hist[ichan])

        # update the spectra
        spect_curr[ichan].setData(freqaxis[freqrange], fft_curr[ichan][freqrange])
        spect_hist[ichan].setData(freqaxis[freqrange], fft_hist[ichan][freqrange])

        # update the plotted lines
        redfreq   = patch.getfloat('input', 'redfreq', default=10. / arguments_freqrange[1])
        redfreq   = EEGsynth.rescale(redfreq, slope=scale_red, offset=offset_red) * arguments_freqrange[1]
        redwidth  = patch.getfloat('input', 'redwidth', default=1. / arguments_freqrange[1])
        redwidth  = EEGsynth.rescale(redwidth, slope=scale_red, offset=offset_red) * arguments_freqrange[1]
        bluefreq  = patch.getfloat('input', 'bluefreq', default=20. / arguments_freqrange[1])
        bluefreq  = EEGsynth.rescale(bluefreq, slope=scale_blue, offset=offset_blue) * arguments_freqrange[1]
        bluewidth = patch.getfloat('input', 'bluewidth', default=4. / arguments_freqrange[1])
        bluewidth = EEGsynth.rescale(bluewidth, slope=scale_blue, offset=offset_blue) * arguments_freqrange[1]

        if showred:
            redleft_curr[ichan].setData(x=[redfreq - redwidth, redfreq - redwidth], y=[specmin_curr[ichan], specmax_curr[ichan]])
            redright_curr[ichan].setData(x=[redfreq + redwidth, redfreq + redwidth], y=[specmin_curr[ichan], specmax_curr[ichan]])
        if showblue:
            blueleft_curr[ichan].setData(x=[bluefreq - bluewidth, bluefreq - bluewidth], y=[specmin_curr[ichan], specmax_curr[ichan]])
            blueright_curr[ichan].setData(x=[bluefreq + bluewidth, bluefreq + bluewidth], y=[specmin_curr[ichan], specmax_curr[ichan]])
        if showred:
            redleft_hist[ichan].setData(x=[redfreq - redwidth, redfreq - redwidth], y=[specmin_hist[ichan], specmax_hist[ichan]])
            redright_hist[ichan].setData(x=[redfreq + redwidth, redfreq + redwidth], y=[specmin_hist[ichan], specmax_hist[ichan]])
        if showblue:
            blueleft_hist[ichan].setData(x=[bluefreq - bluewidth, bluefreq - bluewidth], y=[specmin_hist[ichan], specmax_hist[ichan]])
            blueright_hist[ichan].setData(x=[bluefreq + bluewidth, bluefreq + bluewidth], y=[specmin_hist[ichan], specmax_hist[ichan]])

    # update labels at plotted lines
    if showred:
        text_redleft.setText('%0.1f' % (redfreq - redwidth))
        text_redleft.setPos(redfreq - redwidth, specmax_curr[0])
        text_redright.setText('%0.1f' % (redfreq + redwidth))
        text_redright.setPos(redfreq + redwidth, specmax_curr[0])
    else:
        text_redleft.setText("")
        text_redright.setText("")
    if showblue:
        text_blueleft.setText('%0.1f' % (bluefreq - bluewidth))
        text_blueleft.setPos(bluefreq - bluewidth, specmax_curr[0])
        text_blueright.setText('%0.1f' % (bluefreq + bluewidth))
        text_blueright.setPos(bluefreq + bluewidth, specmax_curr[0])
    else:
        text_blueleft.setText("")
        text_blueright.setText("")

    if showred:
        text_redleft_hist.setText('%0.1f' % (redfreq - redwidth))
        text_redleft_hist.setPos(redfreq - redwidth, specmax_hist[0])
        text_redright_hist.setText('%0.1f' % (redfreq + redwidth))
        text_redright_hist.setPos(redfreq + redwidth, specmax_hist[0])
    else:
        text_redleft_hist.setText("")
        text_redright_hist.setText("")
    if showblue:
        text_blueleft_hist.setText('%0.1f' % (bluefreq - bluewidth))
        text_blueleft_hist.setPos(bluefreq - bluewidth, specmax_hist[0])
        text_blueright_hist.setText('%0.1f' % (bluefreq + bluewidth))
        text_blueright_hist.setPos(bluefreq + bluewidth, specmax_hist[0])
    else:
        text_blueleft_hist.setText("")
        text_blueright_hist.setText("")

    key = "%s.%s.%s" % (prefix, 'redband', 'low')
    patch.setvalue(key, redfreq - redwidth)
    key = "%s.%s.%s" % (prefix, 'redband', 'high')
    patch.setvalue(key, redfreq + redwidth)
    key = "%s.%s.%s" % (prefix, 'blueband', 'low')
    patch.setvalue(key, bluefreq - bluewidth)
    key = "%s.%s.%s" % (prefix, 'blueband', 'high')
    patch.setvalue(key, bluefreq + bluewidth)


# keyboard interrupt handling
def sigint_handler(*args):
    QtGui.QApplication.quit()


signal.signal(signal.SIGINT, sigint_handler)

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(10)                     # timeout in milliseconds
timer.start(int(round(stepsize * 1000)))  # in milliseconds

# Wait until there is enough dat
begsample = -1
while begsample < 0:
    hdr_input = ft_input.getHeader()
    begsample = int(hdr_input.nSamples - window)

# Start
QtGui.QApplication.instance().exec_()
