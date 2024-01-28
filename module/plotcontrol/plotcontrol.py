#!/usr/bin/env python

# Plotcontrol plots the time course of control values
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
import signal
import traceback

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
    global delay, historysize, window, winx, winy, winwidth, winheight, input_name, input_variable, ylim_name, ylim_value, counter, app, win, inputhistory, inputplot, inputcurve, iplot, name, ylim, variable, linecolor, icurve, timer, timeaxis

    # get the options from the configuration file
    delay       = patch.getfloat('general', 'delay')
    window      = patch.getfloat('general', 'window') # in seconds
    winx        = patch.getint('display', 'xpos')
    winy        = patch.getint('display', 'ypos')
    winwidth    = patch.getint('display', 'width')
    winheight   = patch.getint('display', 'height')

    historysize = int(window/delay) # in steps
    timeaxis = np.linspace(-window, 0, historysize)

    input_name, input_variable = list(zip(*patch.config.items('input')))
    ylim_name, ylim_value = list(zip(*patch.config.items('ylim')))

    # count the total number of curves to be drawm
    counter = 0
    for iplot, name in enumerate(input_name):
        for control in input_variable[iplot].split(','):
            counter += 1

    # start the graphical user interface
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(path, '../../doc/figures/logo-128.ico')))
    app.aboutToQuit.connect(_stop)
    signal.signal(signal.SIGINT, _stop)

    # deal with uncaught exceptions
    sys.excepthook = _exception_hook

    win = QtWidgets.QMainWindow()
    win.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plotcontrol'))
    win.setGeometry(winx, winy, winwidth, winheight)
    layout = pg.GraphicsLayoutWidget()
    win.setCentralWidget(layout)

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    # Initialize variables
    inputhistory = np.ones((counter, historysize))
    inputplot    = []
    inputcurve   = []

    # Create panels for each channel
    for iplot, name in enumerate(input_name):
        
        inputplot.append(layout.addPlot(title="%s" % name))
        inputplot[iplot].setLabel('bottom', text = 'Time (s)')
        inputplot[iplot].showGrid(x=False, y=True, alpha=None)

        ylim = patch.getfloat('ylim', name, multiple=True, default=None)
        if ylim==[] or ylim==None:
            monitor.info("Ylim empty, will let it flow")
        else:
            monitor.info("Setting Ylim according to specified range")
            inputplot[iplot].setYRange(ylim[0], ylim[1])

        variable = input_variable[iplot].split(",")
        linecolor = patch.getstring('linecolor', name, multiple=True, default='w,'*len(variable))
        for icurve in range(len(variable)):
            inputcurve.append(inputplot[iplot].plot(pen=linecolor[icurve]))
        layout.nextRow()

    win.show()

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)            # timeout in milliseconds
    timer.start(int(delay * 1000))   # in milliseconds


def _loop_once():
    '''Update the main figure once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global delay, historysize, window, winx, winy, winwidth, winheight, input_name, input_variable, ylim_name, ylim_value, counter, app, win, inputhistory, inputplot, inputcurve, iplot, name, ylim, variable, linecolor, icurve, timer, timeaxis

    monitor.loop()

    if not patch.getint('general', 'enable', default=True):
        # do not read data and do not plot anything
        return

    # shift all historic data with one sample
    inputhistory = np.roll(inputhistory, -1, axis=1)

    counter = 0
    for iplot, name in enumerate(input_name):

        # update the vertical scaling
        ylim = patch.getfloat('ylim', name, multiple=True, default=None)
        if ylim==[] or ylim==None:
            # monitor.info("Ylim empty, will let it flow")
            pass
        else:
            # monitor.info("Setting Ylim according to specified range")
            inputplot[iplot].setYRange(ylim[0], ylim[1])

        # update the current data
        values = patch.getfloat('input', name, multiple=True, default=np.nan)
        for value in values:
            inputhistory[counter, historysize-1] = value
            inputcurve[counter].setData(timeaxis, inputhistory[counter, :])
            counter += 1


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
