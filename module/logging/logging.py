#!/usr/bin/env python

# Graphical dialog that can receive and display logging information
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2023 EEGsynth project
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

import os
import sys

# exclude the eegsynth/module/logging directory from the path
for i, dir in enumerate(sys.path):
    if dir.endswith(os.path.join('module', 'logging')):
        del sys.path[i]
        continue

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSignal

import time
import threading
import signal
import logging

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
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


class TriggerThread(threading.Thread, QObject):
    signal = pyqtSignal(str)
    def __init__(self, redischannel, callback):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.redischannel = redischannel
        self.running = True
        # connect a Qt signal to the append function
        self.signal.connect(callback)
    def stop(self):
        self.running = False
    def run(self):
        pubsub = patch.pubsub()
        pubsub.subscribe('LOGGING_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)  # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    msg = item['data']
                    self.signal.emit(msg)


class QTextEditLogger_v1(logging.Handler):
    """Class that implements a graphical window with full logging capabilities
    """
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class QTextEditLogger_v2():
    """Class that implements a graphical window with a simple append function
    """
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def append(self, msg):
        self.widget.appendPlainText(msg)


class Window(QtWidgets.QDialog, QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth logging'))

        layout = QtWidgets.QVBoxLayout()

        # logTextBox = QTextEditLogger_v1(self)
        # logTextBox.setFormatter(logging.Formatter('%(message)s'))
        # logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        # logTextBox.setFormatter(logging.Formatter('%(levelname)s: %(name)s: %(message)s'))
        # logging.getLogger().addHandler(logTextBox)
        # logging.getLogger().setLevel(logging.DEBUG)
        # layout.addWidget(logTextBox.widget)

        logTextBox = QTextEditLogger_v2(self)
        layout.addWidget(logTextBox.widget)
        self.append = logTextBox.append

        self.setLayout(layout)


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
    global delay, winx, winy, winwidth, winheight, lock, trigger, app, window, timer

    trigger = []

    # get the options from the configuration file
    delay       = patch.getfloat('general', 'delay')
    winx        = patch.getint('display', 'xpos')
    winy        = patch.getint('display', 'ypos')
    winwidth    = patch.getint('display', 'width')
    winheight   = patch.getint('display', 'height')

    # start the graphical user interface
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(path, '../../doc/figures/logo-128.ico')))
    app.aboutToQuit.connect(_stop)
    signal.signal(signal.SIGINT, _stop)

    window = Window()
    window.show()

    # Set timer for update
    timer = QtCore.QTimer()
    timer.timeout.connect(_loop_once)
    timer.setInterval(10)            # timeout in milliseconds
    timer.start(int(delay * 1000))   # in milliseconds

    lock = threading.Lock()

    input = patch.get('input', 'logging')
    for redischannel in input.split(','):
        monitor.info('setting up logging for "%s"' %(redischannel))
        thread = TriggerThread(redischannel, window.append)
        trigger.append(thread)

    # start the thread for each of the notes
    for thread in trigger:
        thread.start()


def _loop_once():
    '''Run the main loop once
    '''
    global monitor, window
    monitor.loop()
    window.update()


def _loop_forever():
    '''Run the main loop forever
    '''
    QApplication.instance().exec_()


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, trigger
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    patch.publish('LOGGING_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    QApplication.quit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
