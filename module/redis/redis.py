#!/usr/bin/env python

# This module emulates a Redis server in pure Python using ZeroMQ
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2023 EEGsynth project
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

import os
import sys

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
import ZmqRedis


def _setup():
    '''Initialize the module
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    # this module should not use remote logging, as it cannot start logging prior to starting up itself
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=None)


def _start():
    '''Start the module
    '''
    global patch, name, path, monitor
    global monitor, broker, server

    # get the options from the configuration file
    broker = patch.get('general', 'broker', default='zeromq')

    if broker=='zeromq':
        monitor.success('starting the zeromq broker')
        port = patch.getint('zeromq', 'port', default=5555)
        server = ZmqRedis.server(port=port)

    elif broker=='redis':
        msg = 'the Redis broker should be started using "redis.sh" or by calling it directly'
        monitor.error(msg)
        raise RuntimeError(msg)

    elif broker=='fake':
        msg = 'the fake broker does not require a server'
        monitor.error(msg)
        raise RuntimeError(msg)

    elif broker=='dummy':
        msg = 'the dummy broker does not require a server'
        monitor.error(msg)
        raise RuntimeError(msg)

    else:
        msg = 'unknown broker'
        monitor.error(msg)
        raise RuntimeError(msg)


def _loop_once():
    '''Run the main loop once
    '''
    pass


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, broker, server
    if broker=='zeromq':
        server.start()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    pass


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
