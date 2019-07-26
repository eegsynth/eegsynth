#!/usr/bin/env python

# This module acts as a VU meter for control signals.
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
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

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import configparser
import argparse
import os
import redis
import sys
import time
import signal
import numpy as np

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--inifile', default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help='optional name of the configuration file')
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print('Error: cannot connect to redis server')
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to selectively show parameters that have changed
def show_change(key, val):
    if (key not in show_change.previous) or (show_change.previous[key]!=val):
        print("%s = %g" % (key, val))
        show_change.previous[key] = val
        return True
    else:
        return False
show_change.previous = {}

# this determines how much debugging information gets printed
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

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setStyleSheet('background-color:black;');
        self.setWindowTitle('EEGsynth vumeter')

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)

        green = QColor(10, 255, 10)
        red = QColor(255, 10, 10)
        black = QColor(0, 0, 0)
        white = QColor(255, 255, 255)

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
                show_change(name, val)

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
                r = QRect(x, pady + (1-val)*bary, barx, val*bary)
                qp.drawRect(r)

            r = QRect(x, pady, barx, bary)
            qp.setPen(white)
            qp.drawText(r, Qt.AlignCenter | Qt.AlignBottom, name)

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
    QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, sigint_handler)

    ex = Window()
    ex.show()

    # Set timer for update
    timer = QTimer()
    timer.timeout.connect(ex.update)
    timer.setInterval(10)            # timeout in milliseconds
    timer.start(int(delay * 1000))   # in milliseconds

    sys.exit(app.exec_())
