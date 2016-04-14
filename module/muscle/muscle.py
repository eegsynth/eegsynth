#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import multiprocessing
import threading
import math
import numpy as np
from nilearn import signal

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
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
        for item in pubsub.listen():
            if not self.running or not item['type'] is 'message':
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

# start the background thread
lock = threading.Lock()
trigger = TriggerThread(r, config)
trigger.start()

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

H = None
while H is None:
    if debug>0:
        print "Waiting for data to arrive..."
    H = ftc.getHeader()
    time.sleep(0.2)

if debug>1:
    print H
    print H.labels

channel_items = config.items('input')
channame = []
chanindx = []
for item in channel_items:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channame.append(item[0])                            # the channel name
    chanindx.append(config.getint('input', item[0])-1)  # the channel number

window = round(config.getfloat('processing','window') * H.fSample)
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

try:
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

        H = ftc.getHeader()
        endsample = H.nSamples - 1
        if endsample<window:
            continue

        begsample = endsample-window+1
        D = ftc.getData([begsample, endsample])

        D = D[:, chanindx]

        if low_pass or high_pass:
            D = signal.butterworth(D, H.fSample, low_pass=low_pass, high_pass=high_pass, order=order)

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

except KeyboardInterrupt:
    print "Closing threads"
    trigger.stop()
    r.publish('MUSCLE_UNBLOCK', 1)
    trigger.join()
    sys.exit()
