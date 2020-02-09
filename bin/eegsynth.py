#!/usr/bin/env python

# This application starts all modules that are specified as a patch, where
# each module is specified with a configuration file. The configuration file
# name must start with the name of an EEGsynth module, optionally followed
# with a "_xxx" or "-xxx" and must have the extension ".ini".
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019-2020 EEGsynth project
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
from multiprocessing import Process

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

# eegsynth/module contains the modules
sys.path.insert(0, os.path.join(path, '..'))
from module import *

# the module starts as soon as it is instantiated
# optional command-line arguments can be passed to specify the ini file
def _start(module, args=None):
    module(args)

def _main():
    """Parse command line options and start the EEGsynth modules for the specified patch.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("inifile", nargs='+', help="configuration file for a patch")
    args = parser.parse_args()

    # start with an empty list of files
    inifiles = []

    for file_or_dir in args.inifile:
        if os.path.isfile(file_or_dir):
            if not file_or_dir.endswith('.ini'):
                raise RuntimeError('the file extension must be .ini')
            inifiles += [file_or_dir]
        else:
            raise RuntimeError('incorrect command line argument ' + file_or_dir)

    # ignore the EEGsynth modules that are not implemented in Python but that do have an ini file
    inifiles = [file for file in inifiles if not file.endswith('redis.ini')]
    inifiles = [file for file in inifiles if not file.endswith('buffer.ini')]
    inifiles = [file for file in inifiles if not file.endswith('openbci2ft.ini')]

    # this will contain a list of processes
    process = []

    for file in inifiles:
        module = os.path.split(file)[-1]        # keep only the filename
        module = os.path.splitext(module)[0]    # remove the ini extension
        module = module.split('-')[0]           # remove whatever comes after a "-" separator

        # convert the string in a reference to the corresponding Module class
        # as soon as the object is instantiated, the module will start
        module = eval(module + '.Executable')
        file = os.path.join(os.getcwd(), file)
        process.append(Process(target=_start, args=(module, ['--inifile', file])))

    for p in process:
        p.start()

    for p in process:
        p.join()

if __name__ == '__main__':
    _main()
