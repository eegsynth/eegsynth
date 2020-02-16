#!/usr/bin/env python

# OutputOSC sends redis data according to OSC protocol
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

import configparser
import argparse
import os
import redis
import sys
import threading
import time

# The required package depends on the Python version, one works for older and the other for newer versions.
# This cannot be handled easily by setup.py during installation, hence we only _try_ to load the module.
if sys.version_info < (3,5):
    try:
        import OSC
        use_old_version = True
    except ImportError:
        # give a warning, not an error, so that eegsynth.py does not fail as a whole
        print('Warning: OSC is required for the outputosc module, please install it with "pip install OSC"')
else:
    try:
        from pythonosc import udp_client
        use_old_version = False
    except ModuleNotFoundError:
        # give a warning, not an error, so that eegsynth.py does not fail as a whole
        print('Warning: pythonosc is required for the outputosc module, please install it with "pip install pythonosc"')

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
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, name, osctopic):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.name = name
        self.osctopic = osctopic
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('OUTPUTOSC_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)     # this message contains the value of interest
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    # map the Redis values to OSC values
                    val = float(item['data'])
                    # the scale and offset options are channel specific
                    scale  = patch.getfloat('scale', self.name, default=1)
                    offset = patch.getfloat('offset', self.name, default=0)
                    # apply the scale and offset
                    val = EEGsynth.rescale(val, slope=scale, offset=offset)

                    monitor.update(self.osctopic, val)
                    with lock:
                        # send it as a string with a space as separator
                        if use_old_version:
                            msg = OSC.OSCMessage(self.osctopic)
                            msg.append(val)
                            s.send(msg)
                        else:
                            s.send_message(self.osctopic, val)


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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, name
    global monitor, debug, s, list_input, list_output, list1, list2, list3, i, j, lock, trigger, key1, key2, key3, this, thread

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    try:
        if use_old_version:
            s = OSC.OSCClient()
            s.connect((patch.getstring('osc','hostname'), patch.getint('osc','port')))
        else:
            s = udp_client.SimpleUDPClient(patch.getstring('osc','hostname'), patch.getint('osc','port'))
        monitor.success('Connected to OSC server')
    except:
        raise RuntimeError("cannot connect to OSC server")

    # keys should be present in both the input and output section of the *.ini file
    list_input  = config.items('input')
    list_output = config.items('output')

    list1 = [] # the key name that matches in the input and output section of the *.ini file
    list2 = [] # the key name in Redis
    list3 = [] # the key name in OSC
    for i in range(len(list_input)):
        for j in range(len(list_output)):
            if list_input[i][0]==list_output[j][0]:
                list1.append(list_input[i][0])  # short name in the ini file
                list2.append(list_input[i][1])  # redis channel
                list3.append(list_output[j][1]) # osc topic

    # this is to prevent two messages from being sent at the same time
    lock = threading.Lock()

    # each of the Redis messages is mapped onto a different OSC topic
    trigger = []
    for key1, key2, key3 in zip(list1, list2, list3):
        this = TriggerThread(key2, key1, key3)
        trigger.append(this)
        monitor.debug('trigger configured for ' + key1)

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global monitor, patch

    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r

    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTOSC_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
