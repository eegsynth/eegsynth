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

channels = patch.getstring('clock', 'channel', multiple=True)
rates = patch.getint('clock', 'rate',  multiple=True)

# prevent concurrency issues between threads
lock = threading.Lock()

# define a callback function
def callback(key, val, options):
    if (options['count'] % options['rate']) == 0:
        # the output key is not the same as the input key
        key = 'd%d.%s' % (options['rate'], options['channel'])
        patch = options['patch']
        # output a trigger on every N-th incoming trigger
        patch.setvalue(key, val, options['debug'])
    options['count'] += 1
    return options

# construct a thread for each of the triggers
dividers = []
for channel in channels:
    for rate in rates:
        # the options dictionary contains all details that are required for the callback
        options             = {};
        options['channel']  = channel
        options['rate']     = rate
        options['patch']    = patch
        options['debug']    = debug>1
        options['count']    = 0
        dividers.append(EEGsynth.waitfor(patch, channel, callback, options, lock=lock))

# start the thread for each of the dividers
for divider in dividers:
    divider.start()
    print divider.get('channel'), divider.get('rate')

try:
    while True:
        time.sleep(1)
        if debug > 0:
            count = 0
            for divider in dividers:
                count += divider.get('count')
            print "count =", count / len(rates)

except KeyboardInterrupt:
    # stop the thread for each of the dividers
    print "Closing threads"
    for divider in dividers:
        divider.stop()
        divider.join()
    sys.exit()
