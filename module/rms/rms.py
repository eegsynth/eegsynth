# Rms calculates the root-mean-square of a signal
#
# Rms is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
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

#!/usr/bin/env python

from nilearn import signal
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import math
import multiprocessing
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
import EEGsynth
import FieldTrip

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

# this determines how much debugging information gets printed
debug = config.getint('general','debug')
# this is the timeout for the FieldTrip buffer
timeout = config.getfloat('fieldtrip','timeout')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

try:
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ftc = FieldTrip.Client()
    ftc.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to FieldTrip buffer"
except:
    print "Error: cannot connect to FieldTrip buffer"
    exit()

class TriggerThread(threading.Thread):
    def __init__(self, r, config):
        threading.Thread.__init__(self)
        self.r = r
        self.config = config
        self.running = True
        lock.acquire()
        self.update = False
        self.minval = None
        self.maxval = None
        self.freeze = False
        lock.release()
    def stop(self):
        self.running = False
    def run(self):
        pubsub = self.r.pubsub()
        pubsub.subscribe(self.config.get('gain_control','recalibrate'))
        pubsub.subscribe(self.config.get('gain_control','freeze'))
        pubsub.subscribe(self.config.get('gain_control','increase'))
        pubsub.subscribe(self.config.get('gain_control','decrease'))
        pubsub.subscribe('MUSCLE_UNBLOCK')  # this message unblocks the redis listen command
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                lock.acquire()
                if item['channel']==self.config.get('gain_control','recalibrate'):
                    if not self.freeze:
                        # this will cause the min/max values to be completely reset
                        self.minval = None
                        self.maxval = None
                        if debug>0:
                            print 'recalibrate', self.minval, self.maxval
                    else:
                        print 'not recalibrating, freeze is on'
                elif item['channel']==self.config.get('gain_control','freeze'):
                    # freeze the automatic adjustment of the gain control
                    # when frozen, the recalibrate should also not be done
                    self.freeze = (int(item['data'])>0)
                    if debug>1:
                        if self.freeze:
                            print 'freeze on'
                        else:
                            print 'freeze off'
                elif item['channel']==self.config.get('gain_control','increase'):
                    # decreasing the min/max values will increase the gain
                    if not self.minval is None:
                        for i, (min, max) in enumerate(zip(self.minval, self.maxval)):
                            range = float(max-min)
                            if range>0:
                                self.minval[i] += range * self.config.getfloat('gain_control','stepsize')
                                self.maxval[i] -= range * self.config.getfloat('gain_control','stepsize')
                    if debug>0:
                        print 'increase', self.minval, self.maxval
                elif item['channel']==self.config.get('gain_control','decrease'):
                    # increasing the min/max values will decrease the gain
                    if not self.minval is None:
                        for i, (min, max) in enumerate(zip(self.minval, self.maxval)):
                            range = float(max-min)
                            if range>0:
                                self.minval[i] -= range * self.config.getfloat('gain_control','stepsize')
                                self.maxval[i] += range * self.config.getfloat('gain_control','stepsize')
                    if debug>0:
                        print 'decrease', self.minval, self.maxval
                self.update = True
                lock.release()

try:
    # start the background thread
    lock = threading.Lock()
    trigger = TriggerThread(r, config)
    trigger.start()

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

    if debug>1:
        print hdr_input
        print hdr_input.labels

    channel_items = config.items('input')
    channame = []
    chanindx = []
    for item in channel_items:
        # channel numbers are one-offset in the ini file, zero-offset in the code
        channame.append(item[0])                            # the channel name
        chanindx.append(config.getint('input', item[0])-1)  # the channel number

    window = round(config.getfloat('processing','window') * hdr_input.fSample)
    order = config.getint('processing', 'order')

    try:
        low_pass = config.getint('processing', 'low_pass')
    except:
        low_pass = None

    try:
        high_pass = config.getint('processing', 'high_pass')
    except:
        high_pass = None

    minval = None
    maxval = None
    freeze = False

    begsample = -1
    endsample = -1

    while True:
        time.sleep(config.getfloat('general','delay'))

        lock.acquire()
        if trigger.update:
            minval = trigger.minval
            maxval = trigger.maxval
            freeze = trigger.freeze
            trigger.update = False
        else:
            trigger.minval = minval
            trigger.maxval = maxval
        lock.release()

        hdr_input = ftc.getHeader()
        if (hdr_input.nSamples-1)<endsample:
            print "Error: buffer reset detected"
            raise SystemExit
        endsample = hdr_input.nSamples - 1
        if endsample<window:
            continue

        begsample = endsample-window+1
        D = ftc.getData([begsample, endsample])

        D = D[:, chanindx]

        if low_pass or high_pass:
            D = signal.butterworth(D, hdr_input.fSample, low_pass=low_pass, high_pass=high_pass, order=order)

        rms = []
        for i in range(0,len(chanindx)):
            rms.append(0)

        for i,chanvec in enumerate(D.transpose()):
            for chanval in chanvec:
                rms[i] += chanval*chanval
            rms[i] = math.sqrt(rms[i])

        if debug>1:
            print rms

        if minval is None:
            minval = rms
        if maxval is None:
            maxval = rms

        if not freeze:
            # update the min/max value for the automatic gain control
            minval = [min(a,b) for (a,b) in zip(rms,minval)]
            maxval = [max(a,b) for (a,b) in zip(rms,maxval)]

        # apply the gain control
        for i,val in enumerate(rms):
            if maxval[i]==minval[i]:
                rms[i] = 0
            else:
                rms[i] = (rms[i]-minval[i])/(maxval[i]-minval[i])

        for name,val in zip(channame, rms):
            # send it as control value: prefix.channelX=val
            key = "%s.%s" % (config.get('output','prefix'), name)
            val = int(127*val)
            r.set(key,val)

except (KeyboardInterrupt, SystemExit):
    print "Closing threads"
    trigger.stop()
    r.publish('MUSCLE_UNBLOCK', 1)
    trigger.join()
    sys.exit()
