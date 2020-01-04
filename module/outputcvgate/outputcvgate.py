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
debug = patch.getint('general', 'debug')
# values between 0 and 1 work well for the duration
duration_scale = patch.getfloat('duration', 'scale', default=1)
duration_offset = patch.getfloat('duration', 'offset', default=0)

try:
    s = serial.Serial(patch.getstring('serial', 'device'), patch.getint('serial', 'baudrate'), timeout=3.0)
    if debug > 0:
        print("Connected to serial port")
except:
    raise RuntimeError("cannot connect to serial port")

# this is to prevent two triggers from being activated at the same time
lock = threading.Lock()


def SetGate(gate, val):
    if debug > 1:
        print("gate%d" % (gate), "=", val)
    lock.acquire()
    s.write('*g%dv%d#' % (gate, val))
    lock.release()


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, gate, duration):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.gate = gate
        self.duration = duration
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
                    # switch to the value specified in the event, it can be 0 or 1
                    val = float(item['data']) > 0
                    SetGate(self.gate, val)
                    if self.duration != None:
                        # schedule a timer to switch it off after the specified duration
                        duration = patch.getfloat('duration', self.duration)
                        duration = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)
                        # some minimal time is needed for the delay
                        duration = EEGsynth.limit(duration, 0.05, float('Inf'))
                        t = threading.Timer(duration, SetGate, args=[self.gate, False])
                        t.start()


trigger = []
for chanindx in range(1, 5):
    chanstr = "gate%d" % chanindx
    try:
        channel = patch.getstring('trigger', chanstr)
        try:
            duration = patch.getstring('duration', chanstr)
            trigger.append(TriggerThread(channel, chanindx, chanstr))
        except:
            trigger.append(TriggerThread(channel, chanindx, None))
        if debug > 0:
            print("configured", channel, chanindx)
    except:
        pass

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        # loop over the control values
        for chanindx in range(1, 5):
            chanstr = "cv%d" % chanindx
            # this returns None when the channel is not present
            chanval = patch.getfloat('input', chanstr)

            if chanval == None:
                # the value is not present in Redis, skip it
                if debug > 2:
                    print(chanstr, 'not available')
                continue

            # the scale and offset options are channel specific
            scale = patch.getfloat('scale', chanstr, default=4095)
            offset = patch.getfloat('offset', chanstr, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            # ensure that it is within limits
            chanval = EEGsynth.limit(chanval, lo=0, hi=4095)
            chanval = int(chanval)

            if debug > 0:
                monitor.update(chanstr, chanval)

            lock.acquire()
            s.write('*c%dv%04d#' % (chanindx, chanval))
            lock.release()

        for chanindx in range(1, 5):
            chanstr = "gate%d" % chanindx
            chanval = patch.getfloat('input', chanstr)

            if chanval == None:
                # the value is not present in Redis, skip it
                if debug > 2:
                    print(chanstr, 'not available')
                continue

            # the scale and offset options are channel specific
            scale = patch.getfloat('scale', chanstr, default=4095)
            offset = patch.getfloat('offset', chanstr, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            # the value for the gate should be 0 or 1
            chanval = int(chanval > 0)

            if debug > 0:
                monitor.update(chanstr, chanval)

            lock.acquire()
            s.write('*g%dv%d#' % (chanindx, chanval))
            lock.release()

except KeyboardInterrupt:
    print("Closing threads")
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTCVGATE_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
