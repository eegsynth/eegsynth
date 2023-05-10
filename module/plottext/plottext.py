#!/usr/bin/env python

# This module acts as a VU meter for control signals.
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

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
import os
import sys
import time
import signal
import numpy as np

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
import colormap as cm

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setStyleSheet('background-color:black;');
        self.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plottext'))
        self.drawmain()

    def drawmain(self):
        # the left side contains the rows, the right side the columns
        leftlayout = QtWidgets.QVBoxLayout()
        rightlayout = QtWidgets.QHBoxLayout()
        mainlayout = QtWidgets.QHBoxLayout()
        mainlayout.addLayout(leftlayout)
        mainlayout.addLayout(rightlayout)
        self.setLayout(mainlayout)
        # the list of items correspond to the text elements
        self.items = []

        for row in range(0, 16):
            section = 'row%d' % (row + 1)
            if patch.config.has_section(section):
                monitor.debug('adding ' + section)
                sectionlayout = QtWidgets.QHBoxLayout()
                self.drawpanel(sectionlayout, patch.config.items(section))
                leftlayout.addLayout(sectionlayout)

        for column in range(0, 16):
            section = 'column%d' % (column + 1)
            if patch.config.has_section(section):
                monitor.debug('adding ' + section)
                sectionlayout = QtWidgets.QVBoxLayout()
                self.drawpanel(sectionlayout, patch.config.items(section))
                rightlayout.addLayout(sectionlayout)
                
    def drawpanel(self, panel, list):
        for item in list:
            # item[0] is the label, item[1] the redis channel
            label = item[0]
            channel = item[1]
            widget = QtWidgets.QLabel()
            widget.setStyleSheet('color: rgb(200,200,200);')
            widget.setAlignment(QtCore.Qt.AlignCenter)
            panel.addWidget(widget)
            if len(channel)==0:
                # this is just an empty placeholder
                pass
            else:
                widget.setText("<unknown>")
                # remember this as a tuple
                self.items.append((label, channel, widget))

    def update(self):
        for item in self.items:
            label   = item[0]
            channel = item[1]
            widget  = item[2]

            # the value can either be a number or a string
            val = patch.redis.get(channel)
            try:
                val = float(val)
            except:
                # keep the string as it is
                pass

            if val==None:
                # the requested Redis channel seems not to be present
                continue
            elif isinstance(val, str):
                val = val
            else:
                # apply the scaling and offset before converting to a string
                scale = patch.getfloat('scale', name, default=1)
                offset = patch.getfloat('offset', name, default=0)
                val = EEGsynth.rescale(val, slope=scale, offset=offset)
                val = "%g" % (val)

            monitor.update(label, val)

            if patch.getint('display', 'showlabel', default=1):
                # show the name as specified in the ini file
                val = label + ' = ' + val

            # hide the widget while its content and fontsize are being updated
            widget.setVisible(False)
            widget.setText(val)
            # update the font size to fill the available space
            font = QtGui.QFont()
            font.setPixelSize(int(0.8 * widget.geometry().height()))
            widget.setFont(font)
            # show the updated widget
            widget.setVisible(True)


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
    global delay, winx, winy, winwidth, winheight, input_name, input_variable, variable, app, window, timer, colormap, labelposition, labelcolor

    # get the options from the configuration file
    delay           = patch.getfloat('general', 'delay')
    winx            = patch.getint('display', 'xpos')
    winy            = patch.getint('display', 'ypos')
    winwidth        = patch.getint('display', 'width')
    winheight       = patch.getint('display', 'height')

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


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
    QApplication.quit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
