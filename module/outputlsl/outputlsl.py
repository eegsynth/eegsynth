#!/usr/bin/env python

# This module translates Redis control values and events to LSL string markers.
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
import random
import redis
import string
import sys
import threading
import time
from pylsl import StreamInfo, StreamOutlet

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


def randomStringDigits(stringLength=6):
    """Generate a random string of digits """
    letters = string.digits
    return ''.join(random.choice(letters) for i in range(stringLength))


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, trigger):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.name = trigger
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        global r, lsl_format, patch, lock, monitor, outlet
        pubsub = r.pubsub()
        pubsub.subscribe('OUTPUTLSL_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)  # this message contains the trigger
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    if lsl_format == 'value':
                        # map the Redis values to LSL marker values
                        val = float(item['data'])
                        # the scale and offset options are channel specific and can be changed on the fly
                        scale = patch.getfloat('scale', self.name, default=127)
                        offset = patch.getfloat('offset', self.name, default=0)
                        val = EEGsynth.rescale(val, slope=scale, offset=offset)
                        # format the value as a string
                        marker = '%g' % (val)
                    else:
                        marker = self.name
                    with lock:
                        monitor.debug(marker)
                        outlet.push_sample([marker])


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
    global monitor, debug, lsl_name, lsl_type, lsl_id, lsl_format, info, outlet, trigger, item, lock, thread, previous_val

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    lsl_name = patch.getstring('lsl', 'name', default='eegsynth')
    lsl_type = patch.getstring('lsl', 'type', default='Markers')
    lsl_id = patch.getstring('lsl', 'id', default=randomStringDigits())
    lsl_format = patch.getstring('lsl', 'format')

    # create an outlet stream
    info = StreamInfo(lsl_name, lsl_type, 1, 0, 'string', lsl_id)
    outlet = StreamOutlet(info)

    # create the background threads that deal with the triggers
    trigger = []
    monitor.info("Setting up threads for each trigger")
    for item in config.items('trigger'):
        trigger.append(TriggerThread(item[1], item[0]))
        monitor.debug(str(item[0]) + " " + str(item[1]) + " OK")

    # this is to prevent two messages from being sent at the same time
    lock = threading.Lock()

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    previous_val = {}
    for item in config.items('control'):
        key = item[0]
        previous_val[key] = None


    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch
    global monitor, debug, lsl_name, lsl_type, lsl_id, lsl_format, info, outlet, trigger, item, lock, thread, previous_val
    global val, marker

    # loop over the control values
    for item in config.items('control'):
        key = item[0]

        val = patch.getfloat('control', key)
        if val is None:
            continue  # it should be skipped when not present in the ini or Redis
        if val == previous_val[key]:
            continue  # it should be skipped when identical to the previous value
        previous_val[key] = val

        if lsl_format == 'value':
            # map the Redis values to LSL marker values
            # the scale and offset options are control channel specific and can be changed on the fly
            scale = patch.getfloat('scale', key, default=127)
            offset = patch.getfloat('offset', key, default=0)
            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            # format the value as a string
            marker = '%g' % (val)
        else:
            marker = key
        with lock:
            monitor.debug(marker)
            outlet.push_sample([marker])

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
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTLSL_UNBLOCK', 1)
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
