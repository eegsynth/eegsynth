#!/usr/bin/env python

# Plotfreq plots spectral data from the buffer and allows interactive selection
# of frequency bands for further processing
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
    global patch, name, path, monitor, ft_host, ft_port, ft_input
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, channels, window, output, clipsize, clipside, stepsize, historysize, lrate, ylim, scale_red, scale_blue, offset_red, offset_blue, winx, winy, winwidth, winheight, prefix, numhistory, freqaxis, history, showred, showblue, filterorder, filter, notchquality, notch, freqrange, app, win, text_redleft_curr, text_redright_curr, text_blueleft_curr, text_blueright_curr, text_redleft_hist, text_redright_hist, text_blueleft_hist, text_blueright_hist, freqplot_curr, freqplot_hist, spect_curr, spect_hist, redleft_curr, redright_curr, blueleft_curr, blueright_curr, redleft_hist, redright_hist, blueleft_hist, blueright_hist, fft_curr, fft_hist, specmax_curr, specmin_curr, specmax_hist, specmin_hist, plotnr, channr, timer, begsample, endsample, taper

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_input = FieldTrip.Client()
        ft_input.connect(ft_host, ft_port)
        monitor.info("Connected to input FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to input FieldTrip buffer")

    # this is the timeout for the FieldTrip buffer
    timeout = patch.getfloat('fieldtrip', 'timeout', default=30)

    hdr_input = None
    start = time.time()
    while hdr_input is None:
        monitor.info("Waiting for data to arrive...")
        if (time.time() - start) > timeout:
            raise RuntimeError("timeout while waiting for data")
        time.sleep(0.1)
        hdr_input = ft_input.getHeader()

    monitor.info("Data arrived")
    monitor.debug(hdr_input)
    monitor.debug(hdr_input.labels)

    # read variables from ini/redis
    channels    = patch.getint('arguments', 'channels', multiple=True)
    window      = patch.getfloat('arguments', 'window', default=5.0)        # in seconds
    clipsize    = patch.getfloat('arguments', 'clipsize', default=0.0)      # in seconds
    clipside    = patch.getstring('arguments', 'clipside', default='left')  # left is in the past, right is in the future
    stepsize    = patch.getfloat('arguments', 'stepsize', default=0.1)      # in seconds
    historysize = patch.getfloat('arguments', 'historysize', default=10)    # in seconds
    lrate       = patch.getfloat('arguments', 'learning_rate', default=0.2)
    scale_red   = patch.getfloat('scale', 'red')
    scale_blue  = patch.getfloat('scale', 'blue')
    offset_red  = patch.getfloat('offset', 'red')
    offset_blue = patch.getfloat('offset', 'blue')
    winx        = patch.getint('display', 'xpos')
    winy        = patch.getint('display', 'ypos')
    winwidth    = patch.getint('display', 'width')
    winheight   = patch.getint('display', 'height')
    prefix      = patch.getstring('output', 'prefix')
    ylim        = patch.getfloat('arguments', 'ylim', multiple=True, default=None)
    output      = patch.getstring('arguments', 'output', default='amplitude')  # amplitude, power or db

    window      = int(round(window * hdr_input.fSample))       # in samples
    clipsize    = int(round(clipsize * hdr_input.fSample))     # in samples
    if clipside == 'left' or clipside == 'right':
        freqaxis = np.fft.fftfreq((window-clipsize), 1. / hdr_input.fSample)
    elif clipside == 'both':
        freqaxis = np.fft.fftfreq((window-2*clipsize), 1. / hdr_input.fSample)
    numhistory  = int(historysize / stepsize)                  # number of observations in the history
    history     = np.zeros((len(channels), freqaxis.shape[0], numhistory))

    # this is used to taper the data prior to Fourier transforming
    if clipside == 'left' or clipside == 'right':
        taper = np.hanning(window-clipsize)
    elif clipside == 'both':
        taper = np.hanning(window-2*clipsize)

    # ideally it should be possible to change these on the fly
    showred     = patch.getint('input', 'showred', default=1)
    showblue    = patch.getint('input', 'showblue', default=1)

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
    win.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plotspectral'))
    win.setGeometry(winx, winy, winwidth, winheight)
    layout = pg.GraphicsLayoutWidget()
    win.setCentralWidget(layout)
    
    # initialize graphical elements
    text_redleft_curr   = pg.TextItem("", anchor=( 1,  0), color='r')
    text_redright_curr  = pg.TextItem("", anchor=( 0,  0), color='r')
    text_blueleft_curr  = pg.TextItem("", anchor=( 1, -1), color='b')
    text_blueright_curr = pg.TextItem("", anchor=( 0, -1), color='b')
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
    for plotnr, channr in enumerate(channels):

        plot = layout.addPlot(title="%s%s" % ('Spectrum channel ', channr))
        # speeds up the initial axis scaling set the range to something different than [0, 0]
        plot.setXRange(0,1)
        plot.setYRange(0,1)

        freqplot_curr.append(plot)
        if output=='amplitude':
            freqplot_curr[plotnr].setLabel('left', text='Amplitude')
        elif output=='power':
            freqplot_curr[plotnr].setLabel('left', text='Power')
        elif output=='db':
            freqplot_curr[plotnr].setLabel('left', text='dB')
        freqplot_curr[plotnr].setLabel('bottom', text='Frequency (Hz)')

        spect_curr.append(freqplot_curr[plotnr].plot(pen='w'))
        redleft_curr.append(freqplot_curr[plotnr].plot(pen='r'))
        redright_curr.append(freqplot_curr[plotnr].plot(pen='r'))
        blueleft_curr.append(freqplot_curr[plotnr].plot(pen='b'))
        blueright_curr.append(freqplot_curr[plotnr].plot(pen='b'))

        plot = layout.addPlot(title="%s%s%s%s%s" % ('Averaged spectrum channel ', channr, ' (', historysize, 's)'))
        # speeds up the initial axis scaling set the range to something different than [0, 0]
        plot.setXRange(0,1)
        plot.setYRange(0,1)

        freqplot_hist.append(plot)

        if output=='amplitude':
            freqplot_hist[plotnr].setLabel('left', text='Amplitude')
        elif output=='power':
            freqplot_hist[plotnr].setLabel('left', text='Power')
        elif output=='db':
            freqplot_hist[plotnr].setLabel('left', text='dB')
        freqplot_hist[plotnr].setLabel('bottom', text='Frequency (Hz)')

        spect_hist.append(freqplot_hist[plotnr].plot(pen='w'))
        redleft_hist.append(freqplot_hist[plotnr].plot(pen='r'))
        redright_hist.append(freqplot_hist[plotnr].plot(pen='r'))
        blueleft_hist.append(freqplot_hist[plotnr].plot(pen='b'))
        blueright_hist.append(freqplot_hist[plotnr].plot(pen='b'))

        # initialize as lists
        specmin_curr.append(None)
        specmax_curr.append(None)
        specmin_hist.append(None)
        specmax_hist.append(None)
        fft_curr.append(None)
        fft_hist.append(None)

        layout.nextRow()

    win.show()

    # print frequency at lines
    freqplot_curr[0].addItem(text_redleft_curr)
    freqplot_curr[0].addItem(text_redright_curr)
    freqplot_curr[0].addItem(text_blueleft_curr)
    freqplot_curr[0].addItem(text_blueright_curr)
    freqplot_hist[0].addItem(text_redleft_hist)
    freqplot_hist[0].addItem(text_redright_hist)
    freqplot_hist[0].addItem(text_blueleft_hist)
    freqplot_hist[0].addItem(text_blueright_hist)

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)                     # timeout in milliseconds
    timer.start(int(round(stepsize * 1000)))  # in milliseconds


def _loop_once():
    '''Update the main figure once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global ft_host, ft_port, ft_input, timeout, hdr_input, start, channels, window, output, clipsize, clipside, stepsize, historysize, lrate, ylim, scale_red, scale_blue, offset_red, offset_blue, winx, winy, winwidth, winheight, prefix, numhistory, freqaxis, history, showred, showblue, filterorder, filter, notchquality, notch, app, win, text_redleft_curr, text_redright_curr, text_blueleft_curr, text_blueright_curr, text_redleft_hist, text_redright_hist, text_blueleft_hist, text_blueright_hist, freqplot_curr, freqplot_hist, spect_curr, spect_hist, redleft_curr, redright_curr, blueleft_curr, blueright_curr, redleft_hist, redright_hist, blueleft_hist, blueright_hist, fft_curr, fft_hist, specmax_curr, specmin_curr, specmax_hist, specmin_hist, plotnr, channr, timer, begsample, endsample, taper
    global dat, arguments_freqrange, freqrange, redfreq, redwidth, bluefreq, bluewidth

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

    # demean the data to prevent spectral leakage
    if patch.getint('arguments', 'demean', default=1):
        dat = detrend(dat, axis=0, type='constant')

    # detrend the data to prevent spectral leakage
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

    # taper the data
    dat = dat * taper[:, np.newaxis]

    # shift the FFT history by one step
    history = np.roll(history, 1, axis=2)

    for plotnr, channr in enumerate(channels):

        # estimate the absolute FFT at the current moment
        if output == 'amplitude':
            fft_curr[plotnr] = abs(np.fft.fft(dat[:, channr-1]))
        elif output == 'power':
            fft_curr[plotnr] = abs(np.fft.fft(dat[:, channr-1]))**2
        elif output == 'db':
            fft_curr[plotnr] = 10*np.log10(abs(np.fft.fft(dat[:, channr-1])))

        # update the FFT history with the current estimate
        history[plotnr, :, numhistory - 1] = fft_curr[plotnr]
        fft_hist = np.mean(history, axis=2)

        # user-selected frequency band
        arguments_freqrange = patch.getfloat('arguments', 'freqrange', multiple=True)
        freqrange = np.greater(freqaxis, arguments_freqrange[0]) & np.less_equal(freqaxis, arguments_freqrange[1])

        if len(ylim) == 2:
            # set a fixed vertical scale
            specmax_curr[plotnr] = ylim[1]
            specmin_curr[plotnr] = ylim[0]
            specmax_hist[plotnr] = ylim[1]
            specmin_hist[plotnr] = ylim[0]
        elif specmax_curr[plotnr] == None:
            # initialize the vertical scale to the min/max
            specmax_curr[plotnr] = max(fft_curr[plotnr][freqrange])
            specmin_curr[plotnr] = min(fft_curr[plotnr][freqrange])
            specmax_hist[plotnr] = max(fft_hist[plotnr][freqrange])
            specmin_hist[plotnr] = min(fft_hist[plotnr][freqrange])
        else:
            # adapt the vertical scale to the running mean of the min/max
            specmax_curr[plotnr] = (1 - lrate) * float(specmax_curr[plotnr]) + lrate * max(fft_curr[plotnr][freqrange])
            specmin_curr[plotnr] = (1 - lrate) * float(specmin_curr[plotnr]) + lrate * min(fft_curr[plotnr][freqrange])
            specmax_hist[plotnr] = (1 - lrate) * float(specmax_hist[plotnr]) + lrate * max(fft_hist[plotnr][freqrange])
            specmin_hist[plotnr] = (1 - lrate) * float(specmin_hist[plotnr]) + lrate * min(fft_hist[plotnr][freqrange])

        # set the horizontal scale
        freqplot_curr[plotnr].setXRange(arguments_freqrange[0], arguments_freqrange[1])
        freqplot_hist[plotnr].setXRange(arguments_freqrange[0], arguments_freqrange[1])

        # set the vertical scale
        freqplot_curr[plotnr].setYRange(specmin_curr[plotnr], specmax_curr[plotnr])
        freqplot_hist[plotnr].setYRange(specmin_hist[plotnr], specmax_hist[plotnr])

        # update the spectra
        spect_curr[plotnr].setData(freqaxis[freqrange], fft_curr[plotnr][freqrange])
        spect_hist[plotnr].setData(freqaxis[freqrange], fft_hist[plotnr][freqrange])

        # update the vertical plotted lines
        if showred:
            redfreq  = patch.getfloat('input', 'redfreq', default=10. / arguments_freqrange[1])
            redfreq  = EEGsynth.rescale(redfreq, slope=scale_red, offset=offset_red) * arguments_freqrange[1]
            redwidth = patch.getfloat('input', 'redwidth', default=1. / arguments_freqrange[1])
            redwidth = EEGsynth.rescale(redwidth, slope=scale_red, offset=offset_red) * arguments_freqrange[1]
            redleft_curr[plotnr].setData(x=[redfreq - redwidth, redfreq - redwidth], y=[specmin_curr[plotnr], specmax_curr[plotnr]])
            redright_curr[plotnr].setData(x=[redfreq + redwidth, redfreq + redwidth], y=[specmin_curr[plotnr], specmax_curr[plotnr]])
            redleft_hist[plotnr].setData(x=[redfreq - redwidth, redfreq - redwidth], y=[specmin_hist[plotnr], specmax_hist[plotnr]])
            redright_hist[plotnr].setData(x=[redfreq + redwidth, redfreq + redwidth], y=[specmin_hist[plotnr], specmax_hist[plotnr]])
            if plotnr == 0:
                # update the labels at the vertical lines
                text_redleft_curr.setText('%0.1f' % (redfreq - redwidth))
                text_redleft_curr.setPos(redfreq - redwidth, specmax_curr[0])
                text_redright_curr.setText('%0.1f' % (redfreq + redwidth))
                text_redright_curr.setPos(redfreq + redwidth, specmax_curr[0])
                text_redleft_hist.setText('%0.1f' % (redfreq - redwidth))
                text_redleft_hist.setPos(redfreq - redwidth, specmax_hist[0])
                text_redright_hist.setText('%0.1f' % (redfreq + redwidth))
                text_redright_hist.setPos(redfreq + redwidth, specmax_hist[0])
            # write the positions of the lines to Redis
            key = "%s.%s.%s" % (prefix, 'redband', 'low')
            patch.setvalue(key, redfreq - redwidth)
            key = "%s.%s.%s" % (prefix, 'redband', 'high')
            patch.setvalue(key, redfreq + redwidth)

        if showblue:
            bluefreq  = patch.getfloat('input', 'bluefreq', default=20. / arguments_freqrange[1])
            bluefreq  = EEGsynth.rescale(bluefreq, slope=scale_blue, offset=offset_blue) * arguments_freqrange[1]
            bluewidth = patch.getfloat('input', 'bluewidth', default=4. / arguments_freqrange[1])
            bluewidth = EEGsynth.rescale(bluewidth, slope=scale_blue, offset=offset_blue) * arguments_freqrange[1]
            blueleft_curr[plotnr].setData(x=[bluefreq - bluewidth, bluefreq - bluewidth], y=[specmin_curr[plotnr], specmax_curr[plotnr]])
            blueright_curr[plotnr].setData(x=[bluefreq + bluewidth, bluefreq + bluewidth], y=[specmin_curr[plotnr], specmax_curr[plotnr]])
            blueleft_hist[plotnr].setData(x=[bluefreq - bluewidth, bluefreq - bluewidth], y=[specmin_hist[plotnr], specmax_hist[plotnr]])
            blueright_hist[plotnr].setData(x=[bluefreq + bluewidth, bluefreq + bluewidth], y=[specmin_hist[plotnr], specmax_hist[plotnr]])
            if plotnr == 0:
                # update the labels at the vertical lines
                text_blueleft_curr.setText('%0.1f' % (bluefreq - bluewidth))
                text_blueleft_curr.setPos(bluefreq - bluewidth, specmax_curr[0])
                text_blueright_curr.setText('%0.1f' % (bluefreq + bluewidth))
                text_blueright_curr.setPos(bluefreq + bluewidth, specmax_curr[0])
                text_blueleft_hist.setText('%0.1f' % (bluefreq - bluewidth))
                text_blueleft_hist.setPos(bluefreq - bluewidth, specmax_hist[0])
                text_blueright_hist.setText('%0.1f' % (bluefreq + bluewidth))
                text_blueright_hist.setPos(bluefreq + bluewidth, specmax_hist[0])
                # write the positions of the lines to Redis
            key = "%s.%s.%s" % (prefix, 'blueband', 'low')
            patch.setvalue(key, bluefreq - bluewidth)
            key = "%s.%s.%s" % (prefix, 'blueband', 'high')
            patch.setvalue(key, bluefreq + bluewidth)


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
