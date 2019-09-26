#!/usr/bin/env python3

# Generatecontrol creates user-defined signals and writes these to Redis
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017-2019 EEGsynth project
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

import configparser
import argparse
import os
import redis
import sys
from PyQt5.QtWidgets import QApplication
# these three modules must be in the same directory as biofeedback.py
from model import Model
from view import View
from controller import Controller

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
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth


parser = argparse.ArgumentParser()
parser.add_argument('-i',
                    '--inifile',
                    default=os.path.join(path,
                                         os.path.splitext(file)[0] + '.ini'),
                    help='optional name of the configuration file')
args = parser.parse_args()
config = configparser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'),
                          port=config.getint('redis','port'), db=0,
                          decode_responses=True)
    r.client_list()
except redis.ConnectionError:
    print('Error: cannot connect to redis server')
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config


class Application(QApplication):
    def __init__(self, sys_argv):
        super(Application, self).__init__(sys_argv)
        self._model = Model(patch, r)
        self._controller = Controller(self._model, patch)
        self._view = View(self._model, self._controller, patch)
        self._view.show()


if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())
