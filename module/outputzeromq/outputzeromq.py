#!/usr/bin/env python

# This module translates Redis controls to ZeroMQ messages.
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
import zmq

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
sys.path.insert(0,os.path.join(path, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

if not 'general' in config:
    raise RuntimeError("cannot read configuration from " + args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

try:
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%i" % config.getint('zeromq', 'port'))
    socket.send_string('Hello')
except:
    raise RuntimeError("cannot connect to ZeroMQ")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug = patch.getint('general', 'debug')

# keys should be present in both the input and output section of the *.ini file
list_input  = config.items('input')
list_output = config.items('output')

list1 = [] # the key name that matches in the input and output section of the *.ini file
list2 = [] # the key name in Redis
list3 = [] # the key name in ZeroMQ
for i in range(len(list_input)):
    for j in range(len(list_output)):
        if list_input[i][0]==list_output[j][0]:
            list1.append(list_input[i][0])  # short name in the ini file
            list2.append(list_input[i][1])  # redis channel
            list3.append(list_output[j][1]) # zeromq topic

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, name, zeromqtopic):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.name = name
        self.zeromqtopic = zeromqtopic
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('OUTPUTZEROMQ_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)       # this message contains the value of interest
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    # map the Redis values to ZeroMQ values
                    val = float(item['data'])
                    # the scale and offset options are channel specific
                    scale  = patch.getfloat('scale', self.name, default=1)
                    offset = patch.getfloat('offset', self.name, default=0)
                    # apply the scale and offset
                    val = EEGsynth.rescale(val, slope=scale, offset=offset)

                    monitor.update(self.zeromqtopic, val)
                    with lock:
                        # send it as a string with a space as separator
                        socket.send_string("%s %f" % (self.zeromqtopic, val))


# each of the Redis messages is mapped onto a different ZeroMQ topic
trigger = []
for key1, key2, key3 in zip(list1, list2, list3):
    this = TriggerThread(key2, key1, key3)
    trigger.append(this)
    monitor.debug('trigger configured for ' + key1)

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

except KeyboardInterrupt:
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTZEROMQ_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    context.destroy()
    sys.exit()
