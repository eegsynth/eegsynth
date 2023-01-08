#!/usr/bin/env python

# This application starts all modules in a patch. Each module corresponds
# to an ini file that is specified on the command-line. The ini files must
# start with the name of the corresponding module and can optionally be followed
# with a "_xxx" or "-xxx". This allows multiple instances of the same module
# to be started. All ini files should have the extension ".ini".
#
# For example:
#   eegsynth.py generatesignal.ini buffer-1972.ini preprocessing.ini buffer-1973.ini plotsignal.ini
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
from glob import glob
import multiprocessing
import signal
from importlib import import_module

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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

# eegsynth/module contains the modules
sys.path.insert(0, os.path.join(path, '..'))
# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../lib'))
import EEGsynth

# this will contain a list of modules and processes
modules = []
processes = []

def _setup():
    global monitor, modules, processes

    # parse command-line options and determine the list of ini files
    parser = argparse.ArgumentParser()
    parser.add_argument("--general-broker", default=None, help="general broker")
    parser.add_argument("--general-debug", default=None, help="general debug")
    parser.add_argument("--general-delay", default=None, help="general delay")
    parser.add_argument("inifile", nargs='+', help="configuration file for a patch")
    args = parser.parse_args()

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=None, debug=1)

    # the first results in a list of lists, the second flattens it
    args.inifile = [glob(x) for x in args.inifile]
    args.inifile = [item for sublist in args.inifile for item in sublist]

    if len(args.inifile) == 0:
        raise RuntimeError('You must specify one or multiple ini files.')

    # start with an empty list of files
    inifiles = []

    for file_or_dir in args.inifile:
        if os.path.isfile(file_or_dir):
            if not file_or_dir.endswith('.ini'):
                raise RuntimeError('The ini file extension must be .ini')
            inifiles += [file_or_dir]
        else:
            raise RuntimeError('Incorrect command line argument ' + file_or_dir)

    # convert the command-line arguments in a dict
    args = vars(args)
    # remove empty items
    args = {k: v for k, v in args.items() if v}

    for inifile in inifiles:
        # convert the string in a reference to the corresponding class
        module = os.path.split(inifile)[-1]     # keep only the filename
        module = os.path.splitext(module)[0]    # remove the ini extension
        module = module.split('-')[0]           # remove whatever comes after a "-" separator
        module = module.split('_')[0]           # remove whatever comes after a "_" separator

        # construct the full path
        inifile = os.path.join(os.getcwd(), inifile)

        # pass only the specific ini file
        args['inifile'] = inifile

        # pass all other arguments
        args_to_pass = []
        for k, v in args.items():
            # reformat them back into command-line arguments
            args_to_pass += ['--' + k.replace('_', '-'), v]

        # import the class that implements the specific module from eegsynth/module
        # as soon as an object of the class is instantiated, the module will start
        object = import_module('module.' + module)

        modules.append(module)
        processes.append(multiprocessing.Process(target=_start_module, args=(object.Executable, args_to_pass)))

        # give some feedback
        monitor.success('setting up ' + module + ' with arguments ' + ' '.join(args_to_pass))


def _start_module(module, args=None):
    # the module starts as soon as it is instantiated
    # optional command-line arguments can be passed to specify the ini file
    module(args)


def _start():
    global monitor, modules, processes
    for m,p in zip(modules, processes):
        monitor.success('starting ' + m + ' process')
        p.start()


def _stop(*args):
    global monitor, modules, processes
    for m,p in zip(modules, processes):
        monitor.success('terminating ' + m + ' process')
        p.terminate()
    for m,p in zip(modules, processes):
        monitor.success('joining ' + m + ' process')
        p.join()


if __name__ == '__main__':
    # see https://stackoverflow.com/questions/64174552/what-does-the-process-has-forked-and-you-cannot-use-this-corefoundation-functio
    if sys.version_info >= (3, 0):
        multiprocessing.set_start_method('spawn')

    signal.signal(signal.SIGINT, _stop)

    _setup()
    try:
        _start()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
