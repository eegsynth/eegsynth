#!/usr/bin/env python

# This module allows the user to design a graphical interface with dials (knobs), sliders and buttons.
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

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import configparser
import argparse
import os
import redis
import sys
import time
import signal

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
elif sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
else:
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
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

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# this determines how much debugging information gets printed
debug           = patch.getint('general', 'debug')
prefix          = patch.getstring('output', 'prefix')
output_scale    = patch.getfloat('output', 'scale', default=1./127)
output_offset   = patch.getfloat('output', 'offset', default=0.)
winx            = patch.getfloat('display', 'xpos')
winy            = patch.getfloat('display', 'ypos')
winwidth        = patch.getfloat('display', 'width')
winheight       = patch.getfloat('display', 'height')

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setStyleSheet('background-color:black;');
        self.setWindowTitle('EEGsynth inputcontrol')
        self.drawmain()

    # each row or column with sliders/dials/buttons is a panel
    def drawpanel(self, panel, list):
        for item in list:

            try:
                # read the previous value from Redis
                key = '%s.%s' % (prefix, item[0])
                val = float(patch.redis.get(key))
                # sliders and dials have an internal value between 0 and 127
                val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset, reverse=True)
                # buttons have an internal value of 0, 1, 2, 3, 4
                if item[1]=='slap':
                    val = int(1. * val / 127.)
                elif item[1]=='toggle1':
                    val = int(1. * val / 127.)
                elif item[1]=='toggle2':
                    val = int(2. * val / 127.)
                elif item[1]=='toggle3':
                    val = int(3. * val / 127.)
                elif item[1]=='toggle4':
                    val = int(4. * val / 127.)
                if debug>0:
                    print('%s = %g' % (key, val))
            except:
                # set the default initial value to 0
                val = 0

            if item[1]=='label':
                l = QLabel(item[0])
                l.setAlignment(Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                panel.addWidget(l)

            elif item[1]=='text':
                t = QLineEdit()
                t.name = item[0]
                t.type = item[1]
                t.setText("%d" % val)
                t.setAlignment(Qt.AlignHCenter)
                t.setStyleSheet('background-color: rgb(64,64,64); color: rgb(200,200,200);')
                t.editingFinished.connect(self.changevalue)
                l = QLabel(t.name)
                l.setAlignment(Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the slider
                tl = QVBoxLayout()
                tl.addWidget(t)
                tl.setAlignment(t, Qt.AlignHCenter)
                tl.addWidget(l)
                tl.setAlignment(l, Qt.AlignHCenter)
                panel.addLayout(tl)

            elif item[1]=='slider':
                s = QSlider(Qt.Vertical)
                s.name = item[0]
                s.type = item[1]
                s.setMinimum(0)
                s.setMaximum(127) # default is 100
                s.setValue(val)
                s.setTickInterval(1)
                s.setTickPosition(QSlider.NoTicks)
                s.setStyleSheet('background-color: rgb(64,64,64);')
                s.valueChanged.connect(self.changevalue)
                l = QLabel(s.name)
                l.setAlignment(Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the slider
                sl = QVBoxLayout()
                sl.addWidget(s)
                sl.setAlignment(s, Qt.AlignHCenter)
                sl.addWidget(l)
                sl.setAlignment(l, Qt.AlignHCenter)
                panel.addLayout(sl)

            elif item[1]=='dial':
                s = QDial()
                s.name = item[0]
                s.type = item[1]
                s.setMinimum(0)
                s.setMaximum(127) # default is 100
                s.setValue(val)
                s.setStyleSheet('background-color: rgb(64,64,64);')
                s.valueChanged.connect(self.changevalue)
                l = QLabel(s.name)
                l.setAlignment(Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the dial
                sl = QVBoxLayout()
                sl.addWidget(s)
                sl.setAlignment(s, Qt.AlignHCenter)
                sl.addWidget(l)
                sl.setAlignment(l, Qt.AlignHCenter)
                panel.addLayout(sl)

            elif item[1] in ['push', 'slap', 'toggle1', 'toggle2', 'toggle3', 'toggle4']:
                b = QPushButton(item[0])
                b.name = item[0]
                b.type = item[1]
                b.value = val
                if item[1]=='slap' or item[1]=='push':
                    b.pressed.connect(self.changevalue)  # push down
                    b.released.connect(self.changevalue) # release
                else:
                    b.pressed.connect(self.changevalue)  # push down
                    b.released.connect(self.changecolor) # release
                self.setcolor(b)
                panel.addWidget(b)

    def drawmain(self):
        # the left contains the rows, the right the columns
        leftlayout  = QVBoxLayout()
        rightlayout = QHBoxLayout()
        mainlayout  = QHBoxLayout()
        mainlayout.addLayout(leftlayout)
        mainlayout.addLayout(rightlayout)
        self.setLayout(mainlayout)

        # the section 'slider' is treated as the first row
        # this is only for backward compatibility
        section = 'slider'
        if config.has_section(section):
            sectionlayout = QHBoxLayout()
            self.drawpanel(sectionlayout, config.items(section))
            leftlayout.addLayout(sectionlayout)

        for row in range(0,16):
            section = 'row%d' % (row+1)
            if config.has_section(section):
                sectionlayout = QHBoxLayout()
                self.drawpanel(sectionlayout, config.items(section))
                leftlayout.addLayout(sectionlayout)

        # the section 'button' is treated as the first column
        # this is only for backward compatibility
        section = 'button'
        if config.has_section(section):
            sectionlayout = QVBoxLayout()
            self.drawpanel(sectionlayout, config.items(section))
            rightlayout.addLayout(sectionlayout)

        for column in range(0,16):
            section = 'column%d' % (column+1)
            if config.has_section(section):
                sectionlayout = QVBoxLayout()
                self.drawpanel(sectionlayout, config.items(section))
                rightlayout.addLayout(sectionlayout)


    def changecolor(self):
        target = self.sender()
        self.setcolor(target)

    def changevalue(self):
        target = self.sender()
        send = True
        if target.type=='slider' or target.type=='dial':
            val = target.value()
        elif target.type=='text':
            val = float(target.text())  # convert the string into a scalar
            target.setText('%g' % val)  # ensure that the displayed value is consistent
        elif target.type=='slap':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
            send = val>0 # only send the press, not the release
        elif target.type=='push':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
        elif target.type=='toggle1':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
        elif target.type=='toggle2':
            target.value = (target.value + 1) % 3
            val = target.value * 127 / 2
        elif target.type=='toggle3':
            target.value = (target.value + 1) % 4
            val = target.value * 127 / 3
        elif target.type=='toggle4':
            target.value = (target.value + 1) % 5
            val = target.value * 127 / 4
        self.setcolor(target)
        if send:
            key = '%s.%s' % (prefix, target.name)
            val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
            patch.setvalue(key, val, debug=debug)

    def setcolor(self, target):
        # see https://www.w3schools.com/css/css3_buttons.asp
        grey   = 'background-color: rgb(250,250,250); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        red    = 'background-color: rgb(255,0,0);     border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        yellow = 'background-color: rgb(250,250,60);  border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        green  = 'background-color: rgb(60,200,60);   border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        amber  = 'background-color: rgb(250,190,45);  border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'

        if target.type=='slap':
            if target.value==1:
                target.setStyleSheet(amber);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle1' or target.type=='push':
            if target.value==1:
                target.setStyleSheet(red);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle2':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle3':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            elif target.value==3:
                target.setStyleSheet(green);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle4':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            elif target.value==3:
                target.setStyleSheet(green);
            elif target.value==4:
                target.setStyleSheet(amber);
            else:
                target.setStyleSheet(grey);

        elif target.type=='slap' or target.type=='push':
            target.setStyleSheet(grey);

def sigint_handler(*args):
    # close the application cleanly
    QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, sigint_handler)

    # Let the interpreter run every 200 ms
    # see https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co/6072360#6072360
    timer = QTimer()
    timer.start(400)
    timer.timeout.connect(lambda: None)

    ex = Window()
    ex.show()
    sys.exit(app.exec_())
