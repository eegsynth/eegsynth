#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2022 EEGsynth project
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
import threading
import time

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
        pubsub = patch.pubsub()
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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global channels, dividers, count, triggers, channel, divider, thread

    # get the options from the configuration file
    channels = patch.getstring('clock', 'channel', multiple=True)
    dividers = patch.getint('clock', 'rate', multiple=True)

    # keep track of the number of received triggers
    count = 0

    triggers = []
    for channel in channels:
        for divider in dividers:
            triggers.append(TriggerThread(channel, divider))
            monitor.debug("d%d.%s" % (divider, channel))

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
    global patch, name, path, monitor
    global channels, dividers, count, triggers, channel, divider, thread

    monitor.update("count", count / len(dividers))

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
        time.sleep(1)


def _stop():
    '''Stop and clean up and stop on SystemExit, KeyboardInterrupt
    '''
    global monitor, triggers, r
    monitor.success('Closing threads')
    for thread in triggers:
        thread.stop()
    patch.publish('CLOCKDIVIDER_UNBLOCK', 1)
    for thread in triggers:
        thread.join()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
