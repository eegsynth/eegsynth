#!/usr/bin/env python

# Processtrigger performs basic algorithms upon receiving a trigger
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std, mod
from numpy import random
import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time
import threading

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale, normalizerange, normalizestandard

class TriggerThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        global r, monitor, patch

        in_trigger = patch.getstring('trigger', self.name)

        pubsub = r.pubsub()
        pubsub.subscribe('DELAYTRIGGER_UNBLOCK')  # this message unblocks the Redis listen command
        pubsub.subscribe(in_trigger)              # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == in_trigger:
                    with lock:
                        out_trigger = patch.getstring('output', self.name)
                        val = patch.getfloat('input', self.name)
                        delay = patch.getfloat('delay', self.name)
                        monitor.debug("Triggered: %s --(delay: %s seconds)--> %s (%d)" % (in_trigger, delay, out_trigger, val))
                        time.sleep(patch.getfloat('delay', self.name))
                        monitor.debug("Send: %s --(delay: %s seconds)--> %s (%d)" % (in_trigger, delay, out_trigger, val))
                        patch.setvalue(out_trigger, val)

def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, name
    global monitor, prefix, item, val, input_name, input_variable, output_name, output_variable, lock, trigger, thread

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # show the input trigger names
    input_name, input_variable = list(zip(*config.items('input')))
    monitor.info('===== Triggers =====')
    for name, variable in zip(input_name, input_variable):
        monitor.info(name + ' = ' + variable)

    # show the delays
    delay_name, delay_variable = list(zip(*config.items('delay')))
    monitor.info('===== Delays =====')
    for name, variable in zip(delay_name, delay_variable):
        monitor.info(name + ' = ' + variable)

    # show the output (delayed) trigger names
    output_name, output_variable = list(zip(*config.items('output')))
    monitor.info('===== Delayed Triggers =====')
    for name, variable in zip(output_name, output_variable):
        monitor.info(name + ' = ' + variable)

    # this is to prevent two triggers from being processed at the same time
    lock = threading.Lock()

    # create the background threads that deal with the triggers
    trigger = []
    monitor.debug("Setting up threads for each trigger")
    for name in input_name:
        input_name = patch.getstring('input', name)
        monitor.info("Adding thread for: %s" % (input_name))
        trigger.append(TriggerThread(name))

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    '''
    pass


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('PROCESSTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
