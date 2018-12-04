#!/usr/bin/env python

# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2018 EEGsynth project
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

import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import os
import redis
import serial
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

# for keeping track of the number of received triggers
count = 0


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, rate, lrate):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.rate = rate
        self.lrate = lrate
        self.key = "x%d.%s" % (rate, redischannel)
        self.previous = None  # keep the time of the previous trigger
        self.interval = None  # estimate the interval between triggers
        self.running = True
        self.timer = []

    def stop(self):
        self.running = False

    def run(self):
        global count
        global interval
        pubsub = r.pubsub()
        # this message unblocks the Redis listen command
        pubsub.subscribe('CLOCKMULTIPLIER_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    now = time.time()
                    count += 1          # this is for the total count

                    # cancel all timers that are still running
                    for t in self.timer:
                        t.cancel()
                    self.timer = []

                    if self.previous == None:
                        # not yet possible to estimate the interval
                        self.previous = now
                        continue
                    elif self.interval == None:
                        # first estimate of the interval between triggers
                        self.interval = now - self.previous
                        self.previous = now
                    else:
                        # update the estimate of the interval between triggers
                        # the learning rate determines how fast the interval updates (0=never, 1=immediate)
                        self.interval = (1 - self.lrate) * self.interval + self.lrate * (now - self.previous)
                        self.previous = now

                    val = item['data']
                    # send the first one immediately
                    patch.setvalue(self.key, val)

                    for number in range(1, self.rate):
                        # schedule the subsequent ones after some time
                        delay = number * (self.interval / self.rate)
                        t = threading.Timer(delay, patch.setvalue, args=[self.key, val])
                        t.start()
                        self.timer.append(t)

channel = patch.getstring('clock', 'channel', multiple=True)
multiplier = patch.getint('clock', 'rate',  multiple=True)
learning_rate = patch.getfloat('clock', 'learning_rate')

trigger = []
for chan in channel:
    for mult in multiplier:
        trigger.append(TriggerThread(chan, mult, learning_rate))
        print "x%d.%s" % (mult, chan)

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        time.sleep(1)
        if debug > 0:
            print "count =", count / len(multiplier)

except KeyboardInterrupt:
    print "Closing threads"
    for thread in trigger:
        thread.stop()
    r.publish('CLOCKMULTIPLIER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
