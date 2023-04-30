#!/usr/bin/env python

# This module acts as a VU meter for control signals.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2022 EEGsynth project
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
        self.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth plottopo'))

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)

        w = qp.window().width()
        h = qp.window().height()

        cmap_rgb = np.array(getattr(cm, colormap))*255
        cmap_len = cmap_rgb.shape[0]

        scale_xpos      = patch.getfloat('scale', 'xpos', default=1)
        scale_ypos      = patch.getfloat('scale', 'ypos', default=1)
        scale_value     = patch.getfloat('scale', 'value', default=1)
        scale_diameter  = patch.getfloat('scale', 'diameter', default=0.05)
        offset_xpos     = patch.getfloat('offset', 'xpos', default=0)
        offset_ypos     = patch.getfloat('offset', 'ypos', default=0)
        offset_value    = patch.getfloat('offset', 'value', default=0)
        offset_diameter = patch.getfloat('offset', 'diameter', default=0)

        for name in input_name:
            val      = patch.getfloat('input', name, multiple=True)
            xpos     = EEGsynth.rescale(val[0], slope=scale_xpos, offset=offset_xpos)
            ypos     = EEGsynth.rescale(val[1], slope=scale_ypos, offset=offset_ypos)
            value    = EEGsynth.rescale(val[2], slope=scale_value, offset=offset_value)
            diameter = EEGsynth.rescale(val[3], slope=scale_diameter, offset=offset_diameter)

            monitor.update(name, value)

            # the position of the circle is specified as the upper left
            x =     (xpos - diameter/2)*w
            y = (1 - ypos - diameter/2)*h

            if not value == None and not np.isnan(value):
                value = EEGsynth.limit(value, 0, 1)
                r = np.interp(value*(cmap_len-1), np.arange(0,cmap_len), cmap_rgb[:,0])
                g = np.interp(value*(cmap_len-1), np.arange(0,cmap_len), cmap_rgb[:,1])
                b = np.interp(value*(cmap_len-1), np.arange(0,cmap_len), cmap_rgb[:,2])
                qp.setBrush(QtGui.QColor(r, g, b))
                qp.setPen(QtGui.QColor('white'))
                qp.drawEllipse(x, y, diameter*w, diameter*h)
            else:
                # this is needed as fallback when labelcolor is inverse
                r = 0
                g = 0
                b = 0

            if labelcolor == 'inverse':
                qp.setPen(QtGui.QColor(255-r, 255-g, 255-b))
            elif labelcolor == 'none':
                qp.setPen(QtGui.QColor('transparent'))
            else:
                qp.setPen(QtGui.QColor(labelcolor))

            # the initial position of the label is specified as the center
            x =     (xpos)*w
            y = (1 - ypos)*h
            # this is the dispalcement for left/right/top/bottom alignment
            d = scale_diameter*(w+h)/3

            if labelposition == 'center':
                r = QtCore.QRect(x-100, y-100, 200, 200)
                qp.drawText(r, QtCore.Qt.AlignCenter, name)
            elif labelposition == 'top':
                r = QtCore.QRect(x-100, y-200-d, 200, 200)
                qp.drawText(r, QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter, name)
            elif labelposition == 'bottom':
                r = QtCore.QRect(x-100, y-100+d, 200, 200)
                qp.drawText(r, QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter, name)
            elif labelposition == 'left':
                r = QtCore.QRect(x-200-d, y-100, 200, 200)
                qp.drawText(r, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter , name)
            elif labelposition == 'right':
                r = QtCore.QRect(x+d, y-100, 200, 200)
                qp.drawText(r, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter , name)
            elif labelposition == 'none':
                pass

        qp.end()
        self.show()


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
    colormap        = patch.getstring('display', 'colormap', default='parula')
    labelposition   = patch.getstring('display', 'labelposition', default='center')
    labelcolor      = patch.getstring('display', 'labelcolor', default='inverse')

    # get the input options
    input_name, input_variable = list(zip(*patch.config.items('input')))

    for name,variable in zip(input_name, input_variable):
        monitor.info("%s = %s" % (name, variable))

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
