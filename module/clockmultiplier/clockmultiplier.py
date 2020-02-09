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
                        # it is not yet possible to estimate the interval
                        self.previous = now
                        continue
                    elif self.interval == None:
                        # this is the first estimate of the interval between triggers
                        self.interval = now - self.previous
                        self.previous = now
                    else:
                        # update the estimate of the interval between triggers
                        # the learning rate determines how fast the interval updates (0=never, 1=immediate)
                        self.interval = (1 - self.lrate) * self.interval + self.lrate * (now - self.previous)
                        self.previous = now

                    val = float(item['data'])

                    # send the first one immediately
                    patch.setvalue(self.key, val)

                    # schedule the subsequent ones after some time
                    for number in range(1, self.rate):
                        delay = number * (self.interval / self.rate)
                        t = threading.Timer(delay, patch.setvalue, args=[self.key, val])
                        t.start()
                        self.timer.append(t)


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response
    global patch, monitor, debug, channels, multipliers, lrate, count, triggers, channel, multiplier, thread

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug       = patch.getint('general', 'debug')
    channels    = patch.getstring('clock', 'channel', multiple=True)
    multipliers = patch.getint('clock', 'rate',  multiple=True)
    lrate       = patch.getfloat('clock', 'learning_rate', default=1)

    # for keeping track of the number of received triggers
    count = 0

    triggers = []
    for channel in channels:
        for multiplier in multipliers:
            triggers.append(TriggerThread(channel, multiplier, lrate))
            monitor.debug("x%d.%s" % (multiplier, channel))

    # start the thread for each of the triggers
    for thread in triggers:
        thread.start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response
    global patch, monitor, debug, channels, multipliers, lrate, count, triggers, channel, multiplier, thread

    monitor.loop()
    monitor.update("count", count / len(multipliers))
    time.sleep(1)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, triggers, r

    monitor.success('Closing threads')
    for thread in triggers:
        thread.stop()
    r.publish('CLOCKMULTIPLIER_UNBLOCK', 1)
    for thread in triggers:
        thread.join()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
