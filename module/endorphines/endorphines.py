#!/usr/bin/env python

# Endorphines interfaces with the Endorphines Cargo MIDI-to-CV device
#
# Endorphines is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
#
# Copyright (C) 2017 EEGsynth project
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import mido
import os
import redis
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder,'../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

outputport = EEGsynth.midiwrapper(config)
outputport.open_output()
# del config

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, midichannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.midichannel = midichannel
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('ENDORPHINES_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)      # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    if debug>0:
                        print item
                    if int(item['data'])>0:
                        pitch = int(8191)
                    else:
                        pitch = int(0)
                    msg = mido.Message('pitchwheel', pitch=pitch, channel=self.midichannel)
                    if debug>1:
                        print msg
                    lock.acquire()
                    outputport.send(msg)
                    lock.release()
                    # keep it at the present value for a minimal amount of time
                    time.sleep(patch.getfloat('general','pulselength'))

# each of the gates that can be triggered is mapped onto a different message
gate = []
for channel in range(0, 16):
    # channels are one-offset in the ini file, zero-offset in the code
    name = 'channel{}'.format(channel+1)
    if config.has_option('gate', name):
        # start the background thread that deals with this channel
        this = TriggerThread(patch.getstring('gate', name), channel)
        gate.append(this)
        if debug>1:
            print name, 'OK'

# start the thread for each of the notes
for thread in gate:
    thread.start()

# control values are only relevant when different from the previous value
previous_val = {}
for channel in range(1, 16):
    name = 'channel{}'.format(channel)
    previous_val[name] = None

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        # loop over the control values
        for channel in range(0, 16):
            # channels are one-offset in the ini file, zero-offset in the code
            name = 'channel{}'.format(channel+1)
            val = patch.getfloat('control', name)

            if val is None:
                # the value is not present in Redis, skip it
                if debug>2:
                    print name, 'not available'
                continue

            # the scale and offset options are channel specific
            scale  = patch.getfloat('scale', name, default=1)
            offset = patch.getfloat('offset', name, default=0)
            # map the Redis values to MIDI pitch values
            val = EEGsynth.rescale(val, slope=scale, offset=offset)
            # ensure that it is within limits
            val = EEGsynth.limit(val, lo=-8192, hi=8191)
            val = int(val)

            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            else:
                previous_val[name] = val

            if debug>0:
                print name, val

            # midi channels in the inifile are 1-16, in the code 0-15
            midichannel = channel
            msg = mido.Message('pitchwheel', pitch=val, channel=midichannel)
            if debug>1:
                print msg
            lock.acquire()
            outputport.send(msg)
            lock.release()

except KeyboardInterrupt:
    print 'Closing threads'
    for thread in gate:
        thread.stop()
    r.publish('ENDORPHINES_UNBLOCK', 1)
    for thread in gate:
        thread.join()
    sys.exit()
