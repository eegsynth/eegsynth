#!/usr/bin/env python

# This module acts as a VU meter for control signals.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019 EEGsynth project
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
import argparse
import os
import redis
import sys
import time
import signal
import numpy as np

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
debug           = patch.getint('general', 'debug')
delay           = patch.getfloat('general', 'delay')
winx            = patch.getfloat('display', 'xpos')
winy            = patch.getfloat('display', 'ypos')
winwidth        = patch.getfloat('display', 'width')
winheight       = patch.getfloat('display', 'height')

# get the input options
input_name, input_variable = list(zip(*config.items('input')))

if debug>0:
    for name,variable in zip(input_name, input_variable):
        print("%s = %s" % (name, variable))

class Window(QtGui.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setStyleSheet('background-color:black;');
        self.setWindowTitle('EEGsynth vumeter')

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)

        green = QtGui.QColor(10, 255, 10)
        red = QtGui.QColor(255, 10, 10)
        black = QtGui.QColor(0, 0, 0)
        white = QtGui.QColor(255, 255, 255)

        w = qp.window().width()
        h = qp.window().height()

        # determine the width (x) and height (y) of each bar
        barx = int(w/len(input_name))
        bary = h
        # subtract some padding from each side
        padx = int(barx/10)
        pady = int(h/20)
        barx -= 2*padx
        bary -= 2*pady

        # this is the position for the first bar
        x = padx

        for name in input_name:
            scale = patch.getfloat('scale', name, default=1)
            offset = patch.getfloat('offset', name, default=0)
            val = patch.getfloat('input', name, default=np.nan)
            val = EEGsynth.rescale(val, slope=scale, offset=offset)

            if debug>0:
                monitor.update(name, val)

            threshold = patch.getfloat('threshold', name, default=1)
            threshold = EEGsynth.rescale(threshold, slope=scale, offset=offset)

            if val>=0 and val<=threshold:
                qp.setBrush(green)
                qp.setPen(green)
            else:
                qp.setBrush(red)
                qp.setPen(red)

            if not np.isnan(val):
                val = EEGsynth.limit(val, 0, 1)
                r = QtCore.QRect(x, pady + (1-val)*bary, barx, val*bary)
                qp.drawRect(r)

            r = QtCore.QRect(x, pady, barx, bary)
            qp.setPen(white)
            qp.drawText(r, QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom, name)

            # update the position for the next bar
            x += 2*padx + barx

        # add horizontal lines every 10%
        for i in range(1,10):
            qp.setPen(black)
            y = h - pady - float(i)/10 * bary
            qp.drawLine(0, y, w, y)

        qp.end()
        self.show()

def sigint_handler(*args):
    # close the application cleanly
    QtGui.QApplication.quit()

# start the graphical user interface
app = QtGui.QApplication(sys.argv)
signal.signal(signal.SIGINT, sigint_handler)

ex = Window()
ex.show()

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(ex.update)
timer.setInterval(10)            # timeout in milliseconds
timer.start(int(delay * 1000))   # in milliseconds

sys.exit(app.exec_())
