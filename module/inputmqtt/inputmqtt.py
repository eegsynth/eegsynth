#!/usr/bin/env python

# This module translates MQTT messages to Redis controls.
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
import threading
import time
import paho.mqtt.client as mqtt

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


# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    monitor.info("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    if not msg.topic.startswith('$SYS'):
        try:
            key = msg.topic.replace('/', '.').lower()
            if len(prefix):
                # add the prefix
                key = "%s.%s" % (prefix, key)
            # assume that it is a single scalar value
            val = EEGsynth.rescale(float(msg.payload), slope=output_scale, offset=output_offset)
            monitor.update(key, val)
            patch.setvalue(key, val)
        except:
            pass


# The callback for when the client disconnects
def on_disconnect(client, userdata, rc):
    if rc != 0:
        monitor.info("MQTT disconnected")


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor, client

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    try:
        client = mqtt.Client()
        client.connect(patch.get('mqtt', 'hostname'), patch.getint('mqtt', 'port'), patch.getint('mqtt', 'timeout'))
    except:
        raise RuntimeError("cannot connect to MQTT broker")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor, client, name
    global prefix, output_scale, output_offset, input_channels, channel

    # get the options from the configuration file
    prefix = patch.getstring('output', 'prefix')

    # the scale and offset are used to map OSC values to Redis values
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    input_channels = patch.getstring('input', 'channels', default='#', multiple=True)
    for channel in input_channels:
        monitor.info('subscribed to ' + channel)
        client.subscribe(channel)

    client.loop_start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor, client
    global prefix, output_scale, output_offset, input_channels, channel
    global output_scale, output_offset

    # update the scale and offset
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, client
    monitor.success("Stopping module...")
    client.loop_stop(force=False)
    monitor.success("Done.")


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
