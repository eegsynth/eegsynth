#!/usr/bin/env python

# Plotsignal plots the signal from the FieldTrip buffer over time.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2022 EEGsynth project
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

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import os
import pyqtgraph as pg
import signal
import sys
import time
import traceback
from scipy.signal import detrend

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, channels, winx, winy, winwidth, winheight, window, clipsize, clipside, stepsize, lrate, ylim, hdr_input, start, filterorder, filter, notchquality, notch, app, win, timeplot, curve, curvemax, plotnr, channr, timer, begsample, endsample

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.success('Connected to input FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to input FieldTrip buffer")

    # get the options from the configuration file
    channels    = patch.getint('arguments', 'channels', multiple=True)
    winx        = patch.getint('display', 'xpos')
    winy        = patch.getint('display', 'ypos')
    winwidth    = patch.getint('display', 'width')
    winheight   = patch.getint('display', 'height')
    window      = patch.getfloat('arguments', 'window', default=5.0)        # in seconds
    clipsize    = patch.getfloat('arguments', 'clipsize', default=0.0)      # in seconds
    clipside    = patch.getstring('arguments', 'clipside', default='left')  # left is in the past, right is in the future
    stepsize    = patch.getfloat('arguments', 'stepsize', default=0.1)      # in seconds
    lrate       = patch.getfloat('arguments', 'learning_rate', default=0.2)
    ylim        = patch.getfloat('arguments', 'ylim', multiple=True, default=None)

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info('Waiting for data to arrive...')
        if (time.time() - start) > timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.info('Data arrived')
    monitor.debug(hdr_input)
    monitor.debug(hdr_input.labels)

    window      = int(round(window * hdr_input.fSample))       # in samples
    clipsize    = int(round(clipsize * hdr_input.fSample))     # in samples

    # lowpass, highpass or bandpass are optional
    filter = [np.nan, np.nan]
    if patch.hasitem('arguments', 'bandpass'):
        filter = patch.getfloat('arguments', 'bandpass', multiple=True)
    if patch.hasitem('arguments', 'highpass'):
        filter[0] = patch.getfloat('arguments', 'highpass')
    if patch.hasitem('arguments', 'lowpass'):
        filter[1] = patch.getfloat('arguments', 'lowpass')

    # notch filtering is optional
    notch = patch.getfloat('arguments', 'notch', default=np.nan)

    # determine the filter order and notch filter quality
    filterorder = patch.getfloat('arguments', 'filterorder', default=5)
    notchquality = patch.getfloat('arguments', 'notchquality', default=5) # small is a broad filter, large is a sharp filter

    # wait until there is enough data
    begsample = -1
    while begsample < 0:
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()
        if hdr_input != None:
            begsample = hdr_input.nSamples - window
            endsample = hdr_input.nSamples - 1

    # start the graphical user interface
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(path, '../../doc/figures/logo-128.ico')))
    app.aboutToQuit.connect(_stop)
    signal.signal(signal.SIGINT, _stop)

    # deal with uncaught exceptions
    sys.excepthook = _exception_hook

    win = QtWidgets.QMainWindow()
    win.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plotsignal'))
    win.setGeometry(winx, winy, winwidth, winheight)
    layout = pg.GraphicsLayoutWidget()
    win.setCentralWidget(layout)

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    # Initialize variables
    timeplot = []
    curve    = []
    curvemax = [None]*len(channels)

    # Create panels for each channel
    for plotnr, channr in enumerate(channels):

        timeplot.append(layout.addPlot(title="%s%s" % ('Channel ', channr)))
        timeplot[plotnr].setLabel('left', text='Amplitude')
        timeplot[plotnr].setLabel('bottom', text='Time (s)')
        curve.append(timeplot[plotnr].plot(pen='w'))
        layout.nextRow()

    win.show()

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)                       # timeout in milliseconds
    timer.start(int(round(stepsize * 1000)))    # stepsize in milliseconds


def _loop_once():
    '''Update the main figure once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, channels, winx, winy, winwidth, winheight, window, clipsize, clipside, stepsize, lrate, ylim, hdr_input, start, filterorder, filter, notchquality, notch, app, win, timeplot, curve, curvemax, plotnr, channr, timer, begsample, endsample
    global dat, timeaxis

    monitor.loop()

    if not patch.getint('general', 'enable', default=True):
        # do not read data and do not plot anything
        return

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        monitor.info("buffer reset detected")
        begsample = -1
        while begsample < 0:
            hdr_input = ft_input.getHeader()
            begsample = hdr_input.nSamples - window
            endsample = hdr_input.nSamples - 1

    # get the last available data
    begsample = (hdr_input.nSamples - window)  # the clipsize will be removed after filtering
    endsample = (hdr_input.nSamples - 1)

    monitor.info("reading from sample %d to %d" % (begsample, endsample))

    dat = ft_input.getData([begsample, endsample]).astype(np.double)

    # demean the data before filtering to reduce edge artefacts and to center timecourse
    if patch.getint('arguments', 'demean', default=1):
        dat = detrend(dat, axis=0, type='constant')

    # detrend the data before filtering to reduce edge artefacts and to center timecourse
    # this is rather slow, hence the default is not to detrend
    if patch.getint('arguments', 'detrend', default=0):
        dat = detrend(dat, axis=0, type='linear')

    # apply the low/high/bandpass filtering
    if not np.isnan(filter[0]) and not np.isnan(filter[1]):
        dat = EEGsynth.butter_bandpass_filter(dat.T, filter[0], filter[1], int(hdr_input.fSample), filterorder).T
    elif not np.isnan(filter[0]):
        dat = EEGsynth.butter_highpass_filter(dat.T, filter[0], int(hdr_input.fSample), filterorder).T
    elif not np.isnan(filter[1]):
        dat = EEGsynth.butter_lowpass_filter(dat.T, filter[1], int(hdr_input.fSample), filterorder).T

    # apply the notch filtering
    if not np.isnan(notch) and notch<(hdr_input.fSample/2):
        dat = EEGsynth.notch_filter(dat.T, notch, hdr_input.fSample, notchquality).T # remove the line noise
    if not np.isnan(notch) and 2*notch<(hdr_input.fSample/2):
        dat = EEGsynth.notch_filter(dat.T, 2*notch, hdr_input.fSample, notchquality).T # remove the first harmonic
    if not np.isnan(notch) and 3*notch<(hdr_input.fSample/2):
        dat = EEGsynth.notch_filter(dat.T, 3*notch, hdr_input.fSample, notchquality).T # remove the second harmonic

    # remove the filter padding
    if clipsize > 0:
        if clipside == 'left':
            dat = dat[clipsize:,:]
        elif clipside == 'right':
            dat = dat[:-clipsize,:]
        elif clipside == 'both':
            dat = dat[clipsize:-clipsize,:]

    for plotnr, channr in enumerate(channels):

        # time axis
        if clipside == 'left':
            timeaxis = np.linspace(-(window-clipsize) / hdr_input.fSample, 0, len(dat))
        elif clipside == 'right':
            timeaxis = np.linspace(-window / hdr_input.fSample, -clipsize / hdr_input.fSample, len(dat))
        elif clipside == 'both':
            timeaxis = np.linspace(-(window-clipsize) / hdr_input.fSample, -clipsize / hdr_input.fSample, len(dat))

        # update timecourses
        curve[plotnr].setData(timeaxis, dat[:, channr-1])

        if len(ylim)==2:
            # set the vertical scale to the user-specified limits
            timeplot[plotnr].setYRange(ylim[0], ylim[1])
        else:
            # slowly adapt the vertical scale to the running max
            if curvemax[plotnr]==None:
                curvemax[plotnr] = max(abs(dat[:, channr-1]))
            else:
                curvemax[plotnr] = (1 - lrate) * curvemax[plotnr] + lrate * max(abs(dat[:, channr-1]))
            timeplot[plotnr].setYRange(-curvemax[plotnr], curvemax[plotnr])


def _loop_forever():
    '''Run the main loop forever
    '''
    QtWidgets.QApplication.instance().exec_()


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    QtWidgets.QApplication.quit()


def _exception_hook(type, value, tb):
    '''Stop and clean up the PyQt application on uncaught exception
    '''
    traceback_formated = traceback.format_exception(type, value, tb)
    traceback_string = "".join(traceback_formated)
    print(traceback_string, file=sys.stderr)
    monitor.error('uncaught exception, stopping...')
    _stop()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
