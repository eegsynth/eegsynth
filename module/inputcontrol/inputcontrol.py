#!/usr/bin/env python

# This module allows the user to design a graphical interface with dials (knobs), sliders and buttons.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019-2023 EEGsynth project
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


class QLineEditDrop(QtWidgets.QLineEdit):
    ''' This is a QLineEdit widget that also supports dropping a filename on it
    '''
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.setText(files[0])


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(winx, winy, winwidth, winheight)
        self.setStyleSheet('background-color:black;')
        self.setWindowTitle(patch.getstring('display', 'title', default='EEGsynth inputcontrol'))
        self.drawmain()

    # each row or column with sliders/dials/buttons is a panel
    def drawpanel(self, panel, list):
        for item in list:

            try:
                # get the default or previous value from Redis
                key = '%s.%s' % (prefix, item[0])
                val = patch.redis.get(key)
                # the value can either be a number or a string
                try:
                    val = float(val)
                    # apply the appropriate scaling
                    if item[1] == 'slider' or item[1] == 'dial':
                        # sliders and dials have an internal value between 0 and 127
                        val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset, reverse=True)
                    elif item[1] == 'slap' or item[1] == 'push':
                        # buttons have an internal value of 0, 1, 2, 3, 4 and should always start as 0, see https://github.com/eegsynth/eegsynth/issues/375
                        val = 0
                    elif item[1] == 'toggle1':
                        val = int(1. * val / 127.)
                    elif item[1] == 'toggle2':
                        val = int(2. * val / 127.)
                    elif item[1] == 'toggle3':
                        val = int(3. * val / 127.)
                    elif item[1] == 'toggle4':
                        val = int(4. * val / 127.)
                    elif item[1] == 'text':
                        # text has an internal value identical to the external value
                        val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
                    monitor.info('%s = %g' % (key, val))

                except ValueError:
                    val = val
                    monitor.info('%s = %s' % (key, val))

            except:
                # set the default value to 0
                val = 0

            if item[1] == 'label':
                l = QtWidgets.QLabel(item[0])
                l.setAlignment(QtCore.Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                panel.addWidget(l)

            elif item[1] == 'placeholder':
                l = QtWidgets.QLabel("")
                panel.addWidget(l)

            elif item[1] == 'text':
                t = QLineEditDrop() # derived from QtWidgets.QLineEdit()
                t.name = item[0]
                t.type = item[1]
                # the value can either be a number or a string
                if isinstance(val, str):
                    t.setText(val)
                else:
                    t.setText("%g" % val)
                t.setAlignment(QtCore.Qt.AlignHCenter)
                t.setStyleSheet('background-color: rgb(64,64,64); color: rgb(200,200,200);')
                t.editingFinished.connect(self.changevalue) # upon manual edit
                t.textChanged.connect(self.changevalue)     # upon drag-and-drop
                l = QtWidgets.QLabel(t.name)
                l.setAlignment(QtCore.Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the slider
                tl = QtWidgets.QVBoxLayout()
                tl.addWidget(t)
                tl.setAlignment(t, QtCore.Qt.AlignHCenter)
                tl.addWidget(l)
                tl.setAlignment(l, QtCore.Qt.AlignHCenter)
                panel.addLayout(tl)

            elif item[1] == 'slider':
                s = QtWidgets.QSlider(QtCore.Qt.Vertical)
                s.name = item[0]
                s.type = item[1]
                s.setMinimum(0)
                s.setMaximum(127)  # default is 100
                s.setValue(int(val))
                s.setTickInterval(1)
                s.setTickPosition(QtWidgets.QSlider.NoTicks)
                s.setStyleSheet('background-color: rgb(64,64,64);')
                s.valueChanged.connect(self.changevalue)
                l = QtWidgets.QLabel(s.name)
                l.setAlignment(QtCore.Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the slider
                sl = QtWidgets.QVBoxLayout()
                sl.addWidget(s)
                sl.setAlignment(s, QtCore.Qt.AlignHCenter)
                sl.addWidget(l)
                sl.setAlignment(l, QtCore.Qt.AlignHCenter)
                panel.addLayout(sl)

            elif item[1] == 'dial':
                s = QtWidgets.QDial()
                s.name = item[0]
                s.type = item[1]
                s.setMinimum(0)
                s.setMaximum(127)  # default is 100
                s.setValue(int(val))
                s.setStyleSheet('background-color: rgb(64,64,64);')
                s.valueChanged.connect(self.changevalue)
                l = QtWidgets.QLabel(s.name)
                l.setAlignment(QtCore.Qt.AlignHCenter)
                l.setStyleSheet('color: rgb(200,200,200);')
                # position the label under the dial
                sl = QtWidgets.QVBoxLayout()
                sl.addWidget(s)
                sl.setAlignment(s, QtCore.Qt.AlignHCenter)
                sl.addWidget(l)
                sl.setAlignment(l, QtCore.Qt.AlignHCenter)
                panel.addLayout(sl)

            elif item[1] in ['push', 'slap', 'toggle1', 'toggle2', 'toggle3', 'toggle4']:
                b = QtWidgets.QPushButton(item[0])
                b.name = item[0]
                b.type = item[1]
                b.value = val
                if item[1] == 'slap' or item[1] == 'push':
                    b.pressed.connect(self.changevalue)   # push down
                    b.released.connect(self.changevalue)  # release
                else:
                    b.pressed.connect(self.changevalue)   # push down
                    b.released.connect(self.changecolor)  # release
                self.setcolor(b)
                panel.addWidget(b)

    def drawmain(self):
        # the left contains the rows, the right the columns
        leftlayout = QtWidgets.QVBoxLayout()
        rightlayout = QtWidgets.QHBoxLayout()
        mainlayout = QtWidgets.QHBoxLayout()
        mainlayout.addLayout(leftlayout)
        mainlayout.addLayout(rightlayout)
        self.setLayout(mainlayout)

        # the section 'slider' is treated as the first row
        # this is only for backward compatibility
        section = 'slider'
        if patch.config.has_section(section):
            sectionlayout = QtWidgets.QHBoxLayout()
            self.drawpanel(sectionlayout, patch.config.items(section))
            leftlayout.addLayout(sectionlayout)

        for row in range(0, 16):
            section = 'row%d' % (row + 1)
            if patch.config.has_section(section):
                sectionlayout = QtWidgets.QHBoxLayout()
                self.drawpanel(sectionlayout, patch.config.items(section))
                leftlayout.addLayout(sectionlayout)

        # the section 'button' is treated as the first column
        # this is only for backward compatibility
        section = 'button'
        if patch.config.has_section(section):
            sectionlayout = QtWidgets.QVBoxLayout()
            self.drawpanel(sectionlayout, patch.config.items(section))
            rightlayout.addLayout(sectionlayout)

        for column in range(0, 16):
            section = 'column%d' % (column + 1)
            if patch.config.has_section(section):
                sectionlayout = QtWidgets.QVBoxLayout()
                self.drawpanel(sectionlayout, patch.config.items(section))
                rightlayout.addLayout(sectionlayout)

    def changecolor(self):
        target = self.sender()
        self.setcolor(target)

    def changevalue(self):
        target = self.sender()
        send = True
        if target.type == 'slider' or target.type == 'dial':
            val = target.value()
        elif target.type == 'text':
            # it can either be a number or a string
            try:
                val = float(target.text())  # convert the string into a number
                target.setText('%g' % val)  # ensure that the displayed value is consistent
            except ValueError:
                val = target.text()         # keep it as a string
        elif target.type == 'slap':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
            send = val > 0  # only send the press, not the release
        elif target.type == 'push':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
        elif target.type == 'toggle1':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
        elif target.type == 'toggle2':
            target.value = (target.value + 1) % 3
            val = target.value * 127 / 2
        elif target.type == 'toggle3':
            target.value = (target.value + 1) % 4
            val = target.value * 127 / 3
        elif target.type == 'toggle4':
            target.value = (target.value + 1) % 5
            val = target.value * 127 / 4
        self.setcolor(target)
        if send:
            key = '%s.%s' % (prefix, target.name)
            if target.type != 'text':
                # text has an internal value identical to the external value
                val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
            patch.setvalue(key, val)
            monitor.update(key, val)

    def setcolor(self, target):
        # see https://www.w3schools.com/css/css3_buttons.asp
        grey = 'background-color: rgb(250,250,250); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        red = 'background-color: rgb(255,0,0); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        yellow = 'background-color: rgb(250,250,60); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        green = 'background-color: rgb(60,200,60); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'
        amber = 'background-color: rgb(250,190,45); border: 1px solid gray; border-radius: 4px; padding: 4px 4px;'

        if target.type == 'slap':
            if target.value == 1:
                target.setStyleSheet(amber)
            else:
                target.setStyleSheet(grey)

        elif target.type == 'toggle1' or target.type == 'push':
            if target.value == 1:
                target.setStyleSheet(red)
            else:
                target.setStyleSheet(grey)

        elif target.type == 'toggle2':
            if target.value == 1:
                target.setStyleSheet(red)
            elif target.value == 2:
                target.setStyleSheet(yellow)
            else:
                target.setStyleSheet(grey)

        elif target.type == 'toggle3':
            if target.value == 1:
                target.setStyleSheet(red)
            elif target.value == 2:
                target.setStyleSheet(yellow)
            elif target.value == 3:
                target.setStyleSheet(green)
            else:
                target.setStyleSheet(grey)

        elif target.type == 'toggle4':
            if target.value == 1:
                target.setStyleSheet(red)
            elif target.value == 2:
                target.setStyleSheet(yellow)
            elif target.value == 3:
                target.setStyleSheet(green)
            elif target.value == 4:
                target.setStyleSheet(amber)
            else:
                target.setStyleSheet(grey)

        elif target.type == 'slap' or target.type == 'push':
            target.setStyleSheet(grey)


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
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global prefix, winx, winy, winwidth, winheight, output_scale, output_offset, app, timer

    # get the options from the configuration file
    prefix = patch.getstring('output', 'prefix')
    winx = patch.getint('display', 'xpos')
    winy = patch.getint('display', 'ypos')
    winwidth = patch.getint('display', 'width')
    winheight = patch.getint('display', 'height')

    # the scale and offset are used to map internal values to Redis values
    output_scale = patch.getfloat('output', 'scale', default=1. / 127)  # internal values are from 0 to 127
    output_offset = patch.getfloat('output', 'offset', default=0.)    # internal values are from 0 to 127

    if 'initial' in patch.config.sections():
        # assign the initial values
        for item in patch.config.items('initial'):
            # the value can either be a number or a string
            val = patch.getstring('initial', item[0])
            try:
                # convert to number
                val = float(val)
            except ValueError:
                # keep as string
                val = val
            patch.setvalue(item[0], val)
            monitor.update(item[0], val)

    # start the graphical user interface
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(path, '../../doc/figures/logo-128.ico')))
    app.aboutToQuit.connect(_stop)
    signal.signal(signal.SIGINT, _stop)

    window = Window()
    window.show()

    # Let the interpreter run every 200 ms
    # see https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co/6072360#6072360
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(_loop_once)

    sys.exit(app.exec_())


def _loop_once():
    '''Run the main loop once
    '''
    # Updating the main figure is done through Qt events
    global monitor
    monitor.loop()


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
