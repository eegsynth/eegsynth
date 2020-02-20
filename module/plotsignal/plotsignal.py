#!/usr/bin/env python

# Plotsignal plots the signal from the FieldTrip buffer over time.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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
from scipy.signal import detrend

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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input

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
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.success('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.success('Connected to input FieldTrip buffer')
    except:
        raise RuntimeError("cannot connect to input FieldTrip buffer")


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global channels, winx, winy, winwidth, winheight, window, clipsize, stepsize, lrate, ylim, timeout, hdr_input, start, filtorder, filter, notch, app, win, timeplot, curve, curvemax, plotnr, channr, timer, begsample, endsample

    # read variables from ini/redis
    channels    = patch.getint('arguments', 'channels', multiple=True)
    winx        = patch.getfloat('display', 'xpos')
    winy        = patch.getfloat('display', 'ypos')
    winwidth    = patch.getfloat('display', 'width')
    winheight   = patch.getfloat('display', 'height')
    window      = patch.getfloat('arguments', 'window', default=5.0)        # in seconds
    clipsize    = patch.getfloat('arguments', 'clipsize', default=0.0)      # in seconds
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

    # lowpass, highpass and bandpass are optional, but mutually exclusive
    filtorder = 9
    if patch.hasitem('arguments', 'bandpass'):
        filter = patch.getfloat('arguments', 'bandpass', multiple=True)
    elif patch.hasitem('arguments', 'lowpass'):
        filter = patch.getfloat('arguments', 'lowpass')
        filter = [np.nan, filter]
    elif patch.hasitem('arguments', 'highpass'):
        filter = patch.getfloat('arguments', 'highpass')
        filter = [filter, np.nan]
    else:
        filter = [np.nan, np.nan]

    # notch filtering is optional
    notch = patch.getfloat('arguments', 'notch', default=np.nan)

    # wait until there is enough data
    begsample = -1
    while begsample < 0:
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()
        if hdr_input != None:
            begsample = hdr_input.nSamples - window
            endsample = hdr_input.nSamples - 1

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
    curvemax = [None]*len(channels)

    # Create panels for each channel
    for plotnr, channr in enumerate(channels):

        timeplot.append(win.addPlot(title="%s%s" % ('Channel ', channr)))
        timeplot[plotnr].setLabel('left', text='Amplitude')
        timeplot[plotnr].setLabel('bottom', text='Time (s)')
        curve.append(timeplot[plotnr].plot(pen='w'))
        win.nextRow()

    signal.signal(signal.SIGINT, _stop)

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)                       # timeout in milliseconds
    timer.start(int(round(stepsize * 1000)))    # stepsize in milliseconds


def _loop_once():
    '''Update the main figure once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, ft_host, ft_port, ft_input
    global channels, winx, winy, winwidth, winheight, window, clipsize, stepsize, lrate, ylim, timeout, hdr_input, start, filtorder, filter, notch, app, win, timeplot, curve, curvemax, plotnr, channr, timer, begsample, endsample
    global dat, timeaxis

    monitor.loop()

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples-1)<endsample:
        monitor.info("buffer reset detected")
        begsample = -1
        while begsample < 0:
            hdr_input = ft_input.getHeader()
            begsample = hdr_input.nSamples - window
            endsample = hdr_input.nSamples - 1

    # get the last available data
    begsample = (hdr_input.nSamples - window)  # the clipsize will be removed from both sides after filtering
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

    # apply the user-defined filtering
    if not np.isnan(filter[0]) and not np.isnan(filter[1]):
        dat = EEGsynth.butter_bandpass_filter(dat.T, filter[0], filter[1], int(hdr_input.fSample), filtorder).T
    elif not np.isnan(filter[1]):
        dat = EEGsynth.butter_lowpass_filter(dat.T, filter[1], int(hdr_input.fSample), filtorder).T
    elif not np.isnan(filter[0]):
        dat = EEGsynth.butter_highpass_filter(dat.T, filter[0], int(hdr_input.fSample), filtorder).T
    if not np.isnan(notch):
        dat = EEGsynth.notch_filter(dat.T, notch, hdr_input.fSample).T

    # remove the filter padding
    if clipsize > 0:
        dat = dat[clipsize:-clipsize,:]

    for plotnr, channr in enumerate(channels):

        # time axis
        timeaxis = np.linspace(-(window-2*clipsize) / hdr_input.fSample, 0, len(dat))

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
    QtGui.QApplication.instance().exec_()


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    QtGui.QApplication.quit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
