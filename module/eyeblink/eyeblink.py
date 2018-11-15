#!/usr/bin/env python

# Eyeblink detects eyeblinks
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
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

from nilearn import signal
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
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
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import FieldTrip

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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# this is the timeout for the FieldTrip buffer
timeout = patch.getfloat('fieldtrip','timeout')

try:
    ftc_host = patch.getstring('fieldtrip','hostname')
    ftc_port = patch.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
    if (time.time()-start)>timeout:
        print "Error: timeout while waiting for data"
        raise SystemExit
    hdr_input = ftc.getHeader()
    time.sleep(0.2)

if debug>0:
    print "Data arrived"
if debug>1:
    print hdr_input
    print hdr_input.labels

class TriggerThread(threading.Thread):
    def __init__(self, r, config):
        threading.Thread.__init__(self)
        self.r = r
        self.config = config
        self.running = True
        lock.acquire()
        self.time = 0
        self.last = 0
        lock.release()
    def stop(self):
        self.running = False
    def run(self):
        pubsub = self.r.pubsub()
        channel = self.patch.getstring('processing','calibrate')
        pubsub.subscribe('EYEBLINK_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(channel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                print item['channel'], ":", item['data']
                lock.acquire()
                self.last = self.time
                lock.release()

try:
    # start the background thread
    lock = threading.Lock()
    trigger = TriggerThread(r, config)
    trigger.start()

    channel = patch.getint('input','channel')-1                         # one-offset in the ini file, zero-offset in the code
    window  = round(patch.getfloat('processing','window') * hdr_input.fSample)  # in samples

    minval = None
    maxval = None

    t = 0

    begsample = -1
    endsample = -1

    while True:
        time.sleep(patch.getfloat('processing','window')/10)
        t += 1

        lock.acquire()
        if trigger.last == trigger.time:
            minval = None
            maxval = None
        trigger.time = t
        lock.release()

        hdr_input = ftc.getHeader()
        if (hdr_input.nSamples-1)<endsample:
            print "Error: buffer reset detected"
            raise SystemExit
        endsample = hdr_input.nSamples - 1
        if endsample<window:
            continue

        begsample = endsample - window + 1
        D = ftc.getData([begsample, endsample])
        D = D[:,channel]

        try:
            low_pass = patch.getint('processing', 'low_pass')
        except:
            low_pass = None

        try:
            high_pass = patch.getint('processing', 'high_pass')
        except:
            high_pass = None

        try:
            order = patch.getint('general', 'order')
        except:
            order = None

        # FIXME the following has not been tested yet
        # D = signal.butterworth(D, hdr_input.fSample, low_pass=low_pass, high_pass=high_pass, order=order)

        if minval is None:
            minval = np.min(D)

        if maxval is None:
            maxval = np.max(D)

        minval = min(minval,np.min(D))
        maxval = max(maxval,np.max(D))

        spread = np.max(D) - np.min(D)
        if spread > patch.getfloat('processing','threshold')*(maxval-minval):
            val = 1
        else:
            val = 0

        print('spread ' + str(spread) +
              '\t  max_spread : ' + str(maxval-minval) +
              '\t  output ' + str(val))

        key = "%s.channel%d" % (patch.getstring('output','prefix'), channel+1)
        r.publish(key,val)

except (KeyboardInterrupt, SystemExit):
    print "Closing threads"
    trigger.stop()
    r.publish('EYEBLINK_UNBLOCK', 1)
    trigger.join()
    sys.exit()
