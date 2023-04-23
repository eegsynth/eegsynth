#!/usr/bin/env python

# This graphical user interface (GUI) application starts the modules that comprise a patch.
# Each module corresponds to an ini file that is dropped on the GUI. The ini files must
# start with the name of the corresponding module and can optionally be followed with
# a "_xxx" or "-xxx". This allows multiple instances of the same module to be started.
# All ini files should have the extension ".ini".
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

import sys
import os
import multiprocessing
import signal
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from version import __version__

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))
import EEGsynth

from module import accelerometer, audio2ft, audiomixer, biochill, bitalino2ft, buffer, clockdivider, clockmultiplier, cogito, compressor, csp, delaytrigger, demodulatetone, endorphines, example, generateclock, generatecontrol, generatesignal, generatetrigger, geomixer, heartrate, historycontrol, historysignal, inputcontrol, inputlsl, inputmidi, inputmqtt, inputosc, inputzeromq, keyboard, launchcontrol, launchpad, lsl2ft, modulatetone, outputartnet, outputaudio, outputcvgate, outputdmx, outputlsl, outputmidi, outputmqtt, outputosc, outputzeromq, playbackcontrol, playbacksignal, plotcontrol, plotimage, plotsignal, plotspectral, plottopo, plottrigger, polarbelt, postprocessing, preprocessing, processtrigger, redis, quantizer, recordcontrol, recordsignal, recordtrigger, rms, sampler, sequencer, slewlimiter, sonification, spectral, synthesizer, threshold, unicorn2ft, videoprocessing, volcabass, volcabeats, volcakeys, vumeter

# this will contain a list of modules and processes
modules = []
processes = []


def _start_module(module, args=None):
    # the module starts as soon as it is instantiated
    # optional command-line arguments can be passed to specify the ini file
    module(args)


def _loop_once():
    '''Run the main loop once
    '''
    # Updating the main figure is done through Qt events
    global monitor
    monitor.loop(feedback=60)


def _stop(*args):
    global monitor, modules, processes
    for m,p in zip(modules, processes):
        monitor.success('terminating ' + m + ' process')
        p.terminate()
    for m,p in zip(modules, processes):
        monitor.success('joining ' + m + ' process')
        p.join()
    modules = []
    processes = []
    QApplication.quit()


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(300, 120)
        self.setWindowTitle("EEGsynth %s" % __version__)
        self.setAcceptDrops(True)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        l = QtWidgets.QLabel("Drag and drop your ini files")
        l.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(l)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        inifiles = [u.toLocalFile() for u in event.mimeData().urls()]
        for inifile in inifiles:
            if os.path.splitext(inifile)[1]!='.ini':
                monitor.error('incorrect file', inifile)
                return

            # convert the string in a reference to the corresponding class
            name = os.path.split(inifile)[-1]     # keep only the filename
            name = os.path.splitext(name)[0]    # remove the ini extension
            name = name.split('-')[0]           # remove whatever comes after a "-" separator
            name = name.split('_')[0]           # remove whatever comes after a "_" separator

            # reconstruct the full path
            inifile = os.path.join(os.getcwd(), inifile)

            if   name=='accelerometer':
                module_to_start = accelerometer
            elif name=='audiomixer':
                module_to_start = audiomixer
            elif name=='buffer':
                module_to_start = buffer
            elif name=='bitalino2ft':
                module_to_start = bitalino2ft
            elif name=='clockdivider':
                module_to_start = clockdivider
            elif name=='cogito':
                module_to_start = cogito
            elif name=='csp':
                module_to_start = csp
            elif name=='demodulatetone':
                module_to_start = demodulatetone
            elif name=='example':
                module_to_start = example
            elif name=='generatecontrol':
                module_to_start = generatecontrol
            elif name=='generatetrigger':
                module_to_start = generatetrigger
            elif name=='heartrate':
                module_to_start = heartrate
            elif name=='historysignal':
                module_to_start = historysignal
            elif name=='inputcontrol':
                module_to_start = inputcontrol
            elif name=='inputlsl':
                module_to_start = inputlsl
            elif name=='inputmqtt':
                module_to_start = inputmqtt
            elif name=='inputzeromq':
                module_to_start = inputzeromq
            elif name=='launchcontrol':
                module_to_start = launchcontrol
            elif name=='lsl2ft':
                module_to_start = lsl2ft
            elif name=='openbci2ft':
                module_to_start = openbci2ft
            elif name=='outputaudio':
                module_to_start = outputaudio
            elif name=='outputdmx':
                module_to_start = outputdmx
            elif name=='outputmidi':
                module_to_start = outputmidi
            elif name=='outputosc':
                module_to_start = outputosc
            elif name=='playbackcontrol':
                module_to_start = playbackcontrol
            elif name=='plotcontrol':
                module_to_start = plotcontrol
            elif name=='plotsignal':
                module_to_start = plotsignal
            elif name=='plottopo':
                module_to_start = plottopo
            elif name=='polarbelt':
                module_to_start = polarbelt
            elif name=='preprocessing':
                module_to_start = preprocessing
            elif name=='quantizer':
                module_to_start = quantizer
            elif name=='recordsignal':
                module_to_start = recordsignal
            elif name=='redis':
                module_to_start = redis
            elif name=='sampler':
                module_to_start = sampler
            elif name=='slewlimiter':
                module_to_start = slewlimiter
            elif name=='spectral':
                module_to_start = spectral
            elif name=='threshold':
                module_to_start = threshold
            elif name=='videoprocessing':
                module_to_start = videoprocessing
            elif name=='volcabeats':
                module_to_start = volcabeats
            elif name=='vumeter':
                module_to_start = vumeter
            else:
                monitor.error('incorrect module', name)
                return

            # give some feedback
            args_to_pass = ['--inifile', inifile]

            # give some feedback
            monitor.success(name + ' ' + ' '.join(args_to_pass))

            process = multiprocessing.Process(target=_start_module, args=(module_to_start.Executable, args_to_pass))
            process.start()

            # keep track of all modules and processes
            modules.append(name)
            processes.append(process)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    try:
        # this shows the splash screen and can be used to track parameters that have changed
        monitor = EEGsynth.monitor(name=None, debug=1)
        # initiate the graphical user interface
        app = QApplication(sys.argv)

        app.aboutToQuit.connect(_stop)
        signal.signal(signal.SIGINT,  _stop)
        window = MainWindow()
        window.show()

        # Let the interpreter run every 200 ms
        # see https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co/6072360#6072360
        timer = QtCore.QTimer()
        timer.start(200)
        timer.timeout.connect(_loop_once)

        sys.exit(app.exec_())
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
