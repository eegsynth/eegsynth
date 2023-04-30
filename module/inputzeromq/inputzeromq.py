#!/usr/bin/env python

# This module translates ZeroMQ messages to Redis controls.
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

import os
import string
import sys
import time
import zmq

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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor, context, socket, patch

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    try:
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://%s:%i" % (patch.get('zeromq', 'hostname'), patch.getint('zeromq', 'port')))
    except:
        raise RuntimeError("cannot connect to ZeroMQ")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor, context, socket, patch
    global prefix, output_scale, output_offset, input_channels

    # get the options from the configuration file
    prefix = patch.getstring('output', 'prefix')

    # the scale and offset are used to map OSC values to Redis values
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    input_channels = patch.getstring('input', 'channels', multiple=True)
    if len(input_channels) == 0:
        monitor.info('subscribed to everything')
        socket.setsockopt_string(zmq.SUBSCRIBE, u'')
    else:
        for channel in input_channels:
            monitor.info('subscribed to ' + channel)
            socket.setsockopt_string(zmq.SUBSCRIBE, channel)

    # set a timeout for receiving messages
    socket.RCVTIMEO = int(1000 * patch.getfloat('general', 'delay'))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor, context, socket, patch
    global prefix, output_scale, output_offset, input_channels
    global start

    start = time.time()

    # process all messages that are waiting
    while (time.time() - start) < patch.getfloat('general', 'delay'):
        try:
            # this will timeout after the specified delay
            message = socket.recv_string()
        except zmq.error.Again:
            # timeout, there are no messages
            break
        key, val = message.split()
        key = key.replace('/', '.').lower()
        if len(prefix):
            # add the prefix
            key = "%s.%s" % (prefix, key)
        # assume that it is a single scalar value
        val = EEGsynth.rescale(float(val), slope=output_scale, offset=output_offset)
        monitor.update(key, val)
        patch.setvalue(key, val)

    # update the scale and offset, these values are updated after every delay
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor
    while True:
        monitor.loop()
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, socket, context
    monitor.success("Stopping module...")
    socket.close()
    context.destroy()
    monitor.success("Done.")


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
