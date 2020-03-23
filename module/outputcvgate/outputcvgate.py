#!/usr/bin/env python

# This module outputs Redis data to the Arduino-based CV/Gate output device
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
import serial
import serial.tools.list_ports
from fuzzywuzzy import process

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


def SetControl(chanindx, chanval):
    lock.acquire()
    s.write(b'*c%dv%04d#' % (chanindx, chanval))
    lock.release()


def SetGate(chanindx, chanval):
    lock.acquire()
    s.write(b'*g%dv%d#' % (chanindx, chanval))
    lock.release()


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, chanindx, chanstr):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.chanindx = chanindx
        self.chanstr = chanstr
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        pubsub = r.pubsub()
        # this message unblocks the Redis listen command
        pubsub.subscribe('OUTPUTCVGATE_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    chanval = float(item['data'])

                    if self.chanstr.startswith('cv'):
                        # the value should be between 0 and 4095
                        scale = patch.getfloat('scale', self.chanstr, default=4095)
                        offset = patch.getfloat('offset', self.chanstr, default=0)
                        # apply the scale and offset
                        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
                        chanval = EEGsynth.limit(chanval, lo=0, hi=4095)
                        chanval = int(chanval)
                        SetControl(self.chanindx, chanval)
                        monitor.update(self.chanstr, chanval)

                    elif self.chanstr.startswith('gate'):
                        # the value should be 0 or 1
                        scale = patch.getfloat('scale', self.chanstr, default=1)
                        offset = patch.getfloat('offset', self.chanstr, default=0)
                        # apply the scale and offset
                        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
                        chanval = int(chanval > 0)
                        SetGate(self.chanindx, chanval)
                        monitor.update(self.chanstr, chanval)

                        # schedule a timer to switch the gate off after the specified duration
                        duration = patch.getfloat('duration', self.chanstr, default=None)
                        if duration != None:
                            duration = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)
                            # some minimal time is needed for the delay
                            duration = EEGsynth.limit(duration, 0.05, float('Inf'))
                            t = threading.Timer(duration, SetGate, args=[self.chanindx, False])
                            t.start()


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
    global parser, args, config, r, response, patch
    global monitor, duration_scale, duration_offset, serialdevice, s, lock, trigger, chanindx, chanstr, redischannel, thread

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # values between 0 and 1 work well for the duration
    duration_scale = patch.getfloat('duration', 'scale', default=1)
    duration_offset = patch.getfloat('duration', 'offset', default=0)

    # get the specified serial device, or the one that is the closest match
    serialdevice = patch.getstring('serial', 'device')
    serialdevice = EEGsynth.trimquotes(serialdevice)
    serialdevice = process.extractOne(serialdevice, [comport.device for comport in serial.tools.list_ports.comports()])[0] # select the closest match

    try:
        s = serial.Serial(serialdevice, patch.getint('serial', 'baudrate'), timeout=3.0)
        monitor.success("Connected to serial port")
    except:
        raise RuntimeError("cannot connect to serial port")

    # this is to prevent two triggers from being activated at the same time
    lock = threading.Lock()

    trigger = []
    # configure the trigger threads for the control voltages
    for chanindx in range(1, 5):
        chanstr = "cv%d" % chanindx
        if patch.hasitem('trigger', chanstr):
            redischannel = patch.getstring('trigger', chanstr)
            trigger.append(TriggerThread(redischannel, chanindx, chanstr))
            monitor.info("configured " + redischannel + " on " + str(chanindx))
    # configure the trigger threads for the gates
    for chanindx in range(1, 5):
        chanstr = "gate%d" % chanindx
        if patch.hasitem('trigger', chanstr):
            redischannel = patch.getstring('trigger', chanstr)
            trigger.append(TriggerThread(redischannel, chanindx, chanstr))
            monitor.info("configured " + redischannel + " on " + str(chanindx))

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
    global parser, args, config, r, response, patch
    global monitor, duration_scale, duration_offset, serialdevice, s, lock, trigger, chanindx, chanstr, redischannel, thread

    monitor.loop()
    time.sleep(patch.getfloat('general', 'delay'))

    # loop over the control voltages
    for chanindx in range(1, 5):
        chanstr = "cv%d" % chanindx
        # this returns None when the channel is not present
        chanval = patch.getfloat('input', chanstr)

        if chanval == None:
            # the value is not present in Redis, skip it
            monitor.trace(chanstr, 'not available')
            continue

        # the scale and offset options are channel specific
        scale = patch.getfloat('scale', chanstr, default=4095)
        offset = patch.getfloat('offset', chanstr, default=0)
        # apply the scale and offset
        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
        # ensure that it is within limits
        chanval = EEGsynth.limit(chanval, lo=0, hi=4095)
        chanval = int(chanval)

        SetControl(chanindx, chanval)
        monitor.update(chanstr, chanval)

    # loop over the gates
    for chanindx in range(1, 5):
        chanstr = "gate%d" % chanindx
        chanval = patch.getfloat('input', chanstr)

        if chanval == None:
            # the value is not present in Redis, skip it
            monitor.trace(chanstr, 'not available')
            continue

        # the scale and offset options are channel specific
        scale = patch.getfloat('scale', chanstr, default=4095)
        offset = patch.getfloat('offset', chanstr, default=0)
        # apply the scale and offset
        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
        # the value for the gate should be 0 or 1
        chanval = int(chanval > 0)

        SetGate(chanindx, chanval)
        monitor.update(chanstr, chanval)


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r

    monitor.success("Closing threads")
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTCVGATE_UNBLOCK', 1)
    for thread in trigger:
            thread.join()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
