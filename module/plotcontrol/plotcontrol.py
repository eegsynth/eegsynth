#!/usr/bin/env python

# Plotcontrol plots the time course of control values
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
import signal

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

def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor

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
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor
    global delay, historysize, window, winx, winy, winwidth, winheight, input_name, input_variable, ylim_name, ylim_value, counter, app, win, inputhistory, inputplot, inputcurve, iplot, name, ylim, variable, linecolor, icurve, timer, timeaxis

    # get the options from the configuration file
    delay       = patch.getfloat('general', 'delay')
    window      = patch.getfloat('general', 'window') # in seconds
    winx        = patch.getfloat('display', 'xpos')
    winy        = patch.getfloat('display', 'ypos')
    winwidth    = patch.getfloat('display', 'width')
    winheight   = patch.getfloat('display', 'height')

    historysize = int(window/delay) # in steps
    timeaxis = np.linspace(-window, 0, historysize)

    input_name, input_variable = list(zip(*config.items('input')))
    ylim_name, ylim_value = list(zip(*config.items('ylim')))

    # count the total number of curves to be drawm
    counter = 0
    for iplot, name in enumerate(input_name):
        for control in input_variable[iplot].split(','):
            counter += 1

    # initialize graphical window
    app = QtGui.QApplication([])
    win = pg.GraphicsWindow(title="EEGsynth plotcontrol")
    win.setWindowTitle('EEGsynth plotcontrol')
    win.setGeometry(winx, winy, winwidth, winheight)

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    # Initialize variables
    inputhistory = np.ones((counter, historysize))
    inputplot    = []
    inputcurve   = []

    # Create panels for each channel
    for iplot, name in enumerate(input_name):

        inputplot.append(win.addPlot(title="%s" % name))
        inputplot[iplot].setLabel('bottom', text = 'Time (s)')
        inputplot[iplot].showGrid(x=False, y=True, alpha=0.5)

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

        win.nextRow()

        signal.signal(signal.SIGINT, _stop)

        # Set timer for update
        timer = QtCore.QTimer()
        timer.timeout.connect(_loop_once)
        timer.setInterval(10)            # timeout in milliseconds
        timer.start(int(delay * 1000))   # in milliseconds


def _loop_once():
    '''Update the main figure once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor
    global delay, historysize, window, winx, winy, winwidth, winheight, input_name, input_variable, ylim_name, ylim_value, counter, app, win, inputhistory, inputplot, inputcurve, iplot, name, ylim, variable, linecolor, icurve, timer, timeaxis

    monitor.loop()

    # shift all historic data with one sample
    inputhistory = np.roll(inputhistory, -1, axis=1)

    # update with current data
    counter = 0
    for name in input_name:
        values = patch.getfloat('input', name, multiple=True, default=np.nan)
        for value in values:
            inputhistory[counter, historysize-1] = value
            inputcurve[counter].setData(timeaxis, inputhistory[counter, :])
            counter += 1


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
