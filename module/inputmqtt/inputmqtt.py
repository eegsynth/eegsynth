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

import configparser
import argparse
import os
import redis
import string
import sys
import threading
import time
import paho.mqtt.client as mqtt

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

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

try:
    client = mqtt.Client()
    client.connect(config.get('mqtt', 'hostname'), config.getint('mqtt', 'port'), config.getint('mqtt', 'timeout'))
except:
    raise RuntimeError("cannot connect to MQTT broker")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug = patch.getint('general', 'debug')
prefix = patch.getstring('output', 'prefix')

# the scale and offset are used to map OSC values to Redis values
output_scale = patch.getfloat('output', 'scale', default=1)
output_offset = patch.getfloat('output', 'offset', default=0)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    monitor.info("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
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

def on_disconnect(client, userdata, rc):
    if rc != 0:
        monitor.info("MQTT disconnected")

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

input_channels = patch.getstring('input', 'channels', default='#', multiple=True)
for channel in input_channels:
    monitor.info('subscribed to ' + channel)
    client.subscribe(channel)

client.loop_start()

# keep looping while incoming messages are being handled
try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))
        # update the scale and offset
        output_scale = patch.getfloat('output', 'scale', default=1)
        output_offset = patch.getfloat('output', 'offset', default=0)

except KeyboardInterrupt:
    monitor.success("\nClosing module.")
    client.loop_stop(force=False)
    monitor.success("Done.")
