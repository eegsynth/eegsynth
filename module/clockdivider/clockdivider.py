#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2020 EEGsynth project
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
import serial
import sys
import threading
import time

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

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
channels    = patch.getstring('clock', 'channel', multiple=True)
dividers    = patch.getint('clock', 'rate',  multiple=True)

# keep track of the number of received triggers
count = 0


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, rate):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.rate = rate
        self.key = "d%d.%s" % (rate, redischannel)
        self.count = 0
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        pubsub = r.pubsub()
        global count
        # this message unblocks the Redis listen command
        pubsub.subscribe('CLOCKDIVIDER_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    count += 1          # this is for the total count
                    self.count += 1     # this is for local use
                    if (self.count % self.rate) == 0:
                        val = float(item['data'])
                        patch.setvalue(self.key, val)

triggers = []
for channel in channels:
    for divider in dividers:
        triggers.append(TriggerThread(channel, divider))
        print("d%d.%s" % (divider, channel))

# start the thread for each of the triggers
for thread in triggers:
    thread.start()

try:
    while True:
        time.sleep(1)
        if debug > 0:
            print("count =", count / len(dividers))

except KeyboardInterrupt:
    print("Closing threads")
    for thread in triggers:
        thread.stop()
    r.publish('CLOCKDIVIDER_UNBLOCK', 1)
    for thread in triggers:
        thread.join()
    sys.exit()
