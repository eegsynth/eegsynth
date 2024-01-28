#!/usr/bin/env python

# Plottrigger plots discrete events along a timeline that is continuously scrolling
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2022 EEGsynth project
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
import threading
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


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, number):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.number = number
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = patch.pubsub()
        pubsub.subscribe('PLOTTRIGGER_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)      # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    monitor.debug(item)
                    now = time.time()
                    val = float(item['data'])
                    with lock:
                        # append the time and value as a tuple
                        data[self.number].append((now, val))


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global delay, window, value, winx, winy, winwidth, winheight, data, lock, trigger, number, i, this, thread, app, win, timer, plot

    # get the options from the configuration file
    delay       = patch.getfloat('general', 'delay')            # in seconds
    window      = patch.getfloat('general', 'window')           # in seconds
    value       = patch.getint('general', 'value', default=0)   # boolean
    winx        = patch.getint('display', 'xpos')
    winy        = patch.getint('display', 'ypos')
    winwidth    = patch.getint('display', 'width')
    winheight   = patch.getint('display', 'height')

    # Initialize variables
    data = {}

    # this is to prevent two messages from being sent at the same time
    lock = threading.Lock()

    trigger = []
    number = []
    # each of the gates is mapped onto a different message
    for i in range(1, 17):
        name = 'channel{}'.format(i)
        if patch.config.has_option('gate', name):
            number.append(i)
            data[i] = []
            # start the background thread that deals with this channel
            this = TriggerThread(patch.get('gate', name), i)
            trigger.append(this)
            monitor.info(name + ' trigger configured')
    if len(trigger)==0:
        monitor.warning('no gates were specified in the ini file')

    # start the thread for each of the notes
    for thread in trigger:
        thread.start()

    # start the graphical user interface
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(path, '../../doc/figures/logo-128.ico')))
    app.aboutToQuit.connect(_stop)
    signal.signal(signal.SIGINT, _stop)

    # deal with uncaught exceptions
    sys.excepthook = _exception_hook

    win = QtWidgets.QMainWindow()
    win.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plottrigger'))
    win.setGeometry(winx, winy, winwidth, winheight)
    layout = pg.GraphicsLayoutWidget()
    win.setCentralWidget(layout)

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    plot = layout.addPlot()
    plot.setLabel('left', text='Channel')
    plot.setLabel('bottom', text='Time (s)')
    plot.setXRange(-window, 0)
    plot.setYRange(0.5, len(trigger)+0.5)
    
    win.show()

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)                     # timeout in milliseconds
    timer.start(int(round(delay * 1000)))     # in milliseconds


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global delay, window, value, winx, winy, winwidth, winheight, data, lock, trigger, number, i, this, thread, app, win, timer, plot

    monitor.loop()

    now = time.time()
    plot.clear()
    for y in number:
        for event in data[y]:
            x = event[0] - now      # time
            v = event[1]            # value

            if x < -window-0.5:
                # remove the event if it is too far in the past
                data[y].remove(event)
                continue

            scatter = pg.ScatterPlotItem()
            scatter.addPoints([{'pos': (x, y)}])
            plot.addItem(scatter)

            if value:
                # show the numeric value next to the trigger

                if abs(v-round(v))<0.001:
                    # print it as integer value
                    s = '%d' % v
                else:
                    # print it as floating point value
                    s = '%2.1f' % v

                text = pg.TextItem(s, anchor=(0,0))
                text.setPos(x, y)
                plot.addItem(text)


def _loop_forever():
    '''Run the main loop forever
    '''
    QtWidgets.QApplication.instance().exec_()


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, trigger
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    patch.publish('PLOTTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
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
