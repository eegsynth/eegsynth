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
import argparse
import multiprocessing
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from version import __version__

path = os.path.dirname(os.path.realpath(__file__))
file = os.path.split(__file__)[-1]
name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, 'lib'))
import EEGsynth
import FieldTrip

from module import accelerometer, audio2ft, audiomixer, biochill, bitalino2ft, buffer, clockdivider, clockmultiplier, cogito, compressor, csp, delaytrigger, demodulatetone, endorphines, example, generateclock, generatecontrol, generatesignal, generatetrigger, geomixer, heartrate, historycontrol, historysignal, inputcontrol, inputlsl, inputmidi, inputmqtt, inputosc, inputzeromq, keyboard, launchcontrol, launchpad, logging, lsl2ft, modulatetone, outputartnet, outputaudio, outputcvgate, outputdmx, outputlsl, outputmidi, outputmqtt, outputosc, outputzeromq, pepipiaf, playbackcontrol, playbacksignal, plotcontrol, plotimage, plotsignal, plotspectral, plottext, plottopo, plottrigger, polarbelt, postprocessing, preprocessing, processtrigger, redis, quantizer, recordcontrol, recordsignal, recordtrigger, rms, sampler, sequencer, slewlimiter, sonification, spectral, synthesizer, threshold, unicorn2ft, videoprocessing, volcabass, volcabeats, volcakeys, vumeter

# this will contain a list of modules and processes
modules = []
processes = []

# command-line arguments
args = []

def _setup():
    global args, monitor

    parser = argparse.ArgumentParser(prog='eegsynth-gui',
                    description='This is a graphical user interface to start multiple modules that comprise an EEGsynth patch.',
                    epilog='See https://www.eegsynth.org and https://github.com/eegsynth')
    parser.add_argument("--version", action="version", version="eegsynth %s" % __version__)
    parser.add_argument("--general-broker", default=None, help="general broker")
    parser.add_argument("--general-debug", default=None, help="general debug")
    parser.add_argument("--general-delay", default=None, help="general delay")
    parser.add_argument("--general-logging", default=None, help="general logging, can be 'local' or 'remote'")
    parser.add_argument("--multiprocessing-fork")
    args = parser.parse_args()

    # convert the command-line arguments in a dict
    args = vars(args)
    # remove empty items
    args = {k: v for k, v in args.items() if v}

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=None, debug=1)


def _start_module(module, args=None):
    # the module starts as soon as it is instantiated
    # optional command-line arguments can be passed to specify the ini file
    module(args)

def _loop_once():
    '''Run the main loop once
    '''
    # updating the main figure is done through Qt events
    global monitor, modules, processes
    # remove modules that are not running any more
    keep      = [p.is_alive() for p in processes]
    modules   = [m for (m, k) in zip(modules, keep)   if k]
    processes = [p for (p, k) in zip(processes, keep) if k]
    monitor.loop(feedback=60)
    if len(modules):
        monitor.update('active', ', '.join(modules))
    else:
        monitor.update('active', '<none>')


def _stop(*args):
    global monitor, modules, processes
    if len(modules):
        # stop all modules, starting with the last one
        for m,p in zip(reversed(modules), reversed(processes)):
            monitor.success('terminating ' + m + ' process')
            p.terminate()
        for m,p in zip(reversed(modules), reversed(processes)):
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
        l1 = QtWidgets.QLabel("Drag and drop your ini files here")
        l1.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(l1)
        l2 = QtWidgets.QLabel("")
        l2.setStyleSheet("color: red")
        l2.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(l2)
        b1 = QtWidgets.QPushButton("Stop all modules")
        b1.clicked.connect(self.stopAllModules)
        self.layout.addWidget(b1)
        # remember the label so that it can be changes later
        self.label = l2

    def stopAllModules(self):
        if len(modules):
            # stop all modules, starting with the last one
            for m,p in zip(reversed(modules), reversed(processes)):
                monitor.success('terminating ' + m + ' process')
                p.terminate()
            for m,p in zip(reversed(modules), reversed(processes)):
                monitor.success('joining ' + m + ' process')
                p.join()

    def updateLabel(self):
        if len(modules):
            self.label.setText('\n'.join(modules))
        else:
            self.label.setText('<none>')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        global args

        inifiles = [u.toLocalFile() for u in event.mimeData().urls()]
        for inifile in inifiles:
            if os.path.splitext(inifile)[1]!='.ini':
                monitor.error('incorrect file', inifile)
                continue

            # reconstruct the full path
            inifile = os.path.join(os.getcwd(), inifile)

            # convert the string to the corresponding class
            name = os.path.split(inifile)[-1]   # keep only the filename
            name = os.path.splitext(name)[0]    # remove the ini extension
            fullname = name
            name = name.split('-')[0]           # remove whatever comes after a "-" separator
            name = name.split('_')[0]           # remove whatever comes after a "_" separator

            if fullname in modules:
                monitor.warning('%s is already running, restarting ...' % (fullname))
                index = modules.index(fullname)
                monitor.success('terminating ' + fullname + ' process')
                processes[index].terminate()
                monitor.success('joining ' + fullname + ' process')
                processes[index].join()
                del modules[index]
                del processes[index]

            if name=='accelerometer':
                module_to_start = accelerometer
            elif name=='audio2ft':
                module_to_start = audio2ft
            elif name=='audiomixer':
                module_to_start = audiomixer
            elif name=='biochill':
                module_to_start = biochill
            elif name=='bitalino2ft':
                module_to_start = bitalino2ft
# This requires the brainflow package, which is not installed by default.
#            elif name=='brainflow2ft':
#                module_to_start = brainflow2ft
            elif name=='buffer':
                module_to_start = buffer
            elif name=='clockdivider':
                module_to_start = clockdivider
            elif name=='clockmultiplier':
                module_to_start = clockmultiplier
            elif name=='cogito':
                module_to_start = cogito
# The complexity module has too many dependencies to include by default.
#            elif name=='complexity':
#                module_to_start = complexity
            elif name=='compressor':
                module_to_start = compressor
            elif name=='csp':
                module_to_start = csp
            elif name=='delaytrigger':
                module_to_start = delaytrigger
            elif name=='demodulatetone':
                module_to_start = demodulatetone
            elif name=='endorphines':
                module_to_start = endorphines
            elif name=='example':
                module_to_start = example
            elif name=='generateclock':
                module_to_start = generateclock
            elif name=='generatecontrol':
                module_to_start = generatecontrol
            elif name=='generatesignal':
                module_to_start = generatesignal
            elif name=='generatetrigger':
                module_to_start = generatetrigger
            elif name=='geomixer':
                module_to_start = geomixer
            elif name=='heartrate':
                module_to_start = heartrate
            elif name=='historycontrol':
                module_to_start = historycontrol
            elif name=='historysignal':
                module_to_start = historysignal
            elif name=='inputcontrol':
                module_to_start = inputcontrol
            elif name=='inputlsl':
                module_to_start = inputlsl
            elif name=='inputmidi':
                module_to_start = inputmidi
            elif name=='inputmqtt':
                module_to_start = inputmqtt
            elif name=='inputosc':
                module_to_start = inputosc
            elif name=='inputzeromq':
                module_to_start = inputzeromq
            elif name=='keyboard':
                module_to_start = keyboard
            elif name=='launchcontrol':
                module_to_start = launchcontrol
            elif name=='launchpad':
                module_to_start = launchpad
            elif name=='logging':
                module_to_start = logging
            elif name=='lsl2ft':
                module_to_start = lsl2ft
            elif name=='modulatetone':
                module_to_start = modulatetone
            elif name=='outputartnet':
                module_to_start = outputartnet
            elif name=='outputaudio':
                module_to_start = outputaudio
            elif name=='outputcvgate':
                module_to_start = outputcvgate
            elif name=='outputdmx':
                module_to_start = outputdmx
            elif name=='outputlsl':
                module_to_start = outputlsl
            elif name=='outputmidi':
                module_to_start = outputmidi
            elif name=='outputmqtt':
                module_to_start = outputmqtt
            elif name=='outputosc':
                module_to_start = outputosc
            elif name=='outputzeromq':
                module_to_start = outputzeromq
            elif name=='pepipiaf':
                module_to_start = pepipiaf
            elif name=='playbackcontrol':
                module_to_start = playbackcontrol
            elif name=='playbacksignal':
                module_to_start = playbacksignal
            elif name=='plotcontrol':
                module_to_start = plotcontrol
            elif name=='plotimage':
                module_to_start = plotimage
            elif name=='plotsignal':
                module_to_start = plotsignal
            elif name=='plotspectral':
                module_to_start = plotspectral
            elif name=='plottext':
                module_to_start = plottext
            elif name=='plottopo':
                module_to_start = plottopo
            elif name=='plottrigger':
                module_to_start = plottrigger
            elif name=='polarbelt':
                module_to_start = polarbelt
            elif name=='postprocessing':
                module_to_start = postprocessing
            elif name=='preprocessing':
                module_to_start = preprocessing
            elif name=='processtrigger':
                module_to_start = processtrigger
            elif name=='quantizer':
                module_to_start = quantizer
            elif name=='recordcontrol':
                module_to_start = recordcontrol
            elif name=='recordsignal':
                module_to_start = recordsignal
            elif name=='recordtrigger':
                module_to_start = recordtrigger
            elif name=='redis':
                module_to_start = redis
            elif name=='rms':
                module_to_start = rms
            elif name=='sampler':
                module_to_start = sampler
            elif name=='sequencer':
                module_to_start = sequencer
            elif name=='slewlimiter':
                module_to_start = slewlimiter
            elif name=='sonification':
                module_to_start = sonification
            elif name=='spectral':
                module_to_start = spectral
            elif name=='synthesizer':
                module_to_start = synthesizer
            elif name=='threshold':
                module_to_start = threshold
            elif name=='unicorn2ft':
                module_to_start = unicorn2ft
            elif name=='videoprocessing':
                module_to_start = videoprocessing
            elif name=='volcabass':
                module_to_start = volcabass
            elif name=='volcabeats':
                module_to_start = volcabeats
            elif name=='volcakeys':
                module_to_start = volcakeys
            elif name=='vumeter':
                module_to_start = vumeter
            else:
                monitor.error('incorrect module', name)
                return

            # pass only the specific ini file
            args['inifile'] = inifile

            # pass all other arguments
            args_to_pass = []
            for k, v in args.items():
                # reformat them back into command-line arguments
                args_to_pass += ['--' + k.replace('_', '-'), v]

            # give some feedback
            monitor.success(name + ' ' + ' '.join(args_to_pass))

            process = multiprocessing.Process(target=_start_module, args=(module_to_start.Executable, args_to_pass))
            process.start()

            # keep track of all modules and processes
            modules.append(fullname)
            processes.append(process)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

    _setup()

    try:
        # the icon in the taskbar should not be the python interpreter but the EEGsynth logo
        EEGsynth.appid('org.eegsynth.%s.%s' % (name, __version__))

        # initiate the graphical user interface
        app = QApplication(sys.argv)
        app.setWindowIcon(QtGui.QIcon(os.path.join(path, 'doc/figures/logo-128.ico')))
        app.aboutToQuit.connect(_stop)
        signal.signal(signal.SIGINT,  _stop)

        window = MainWindow()
        window.show()

        # Let the interpreter run every 200 ms
        # see https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co/6072360#6072360
        timer = QtCore.QTimer()
        timer.start(100)
        timer.timeout.connect(_loop_once)
        timer.timeout.connect(window.updateLabel)

        sys.exit(app.exec_())
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
