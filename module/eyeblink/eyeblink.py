#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import threading
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
        self.running = FALSE
    def run(self):
        pubsub = self.r.pubsub()
        channel = self.config.get('processing','calibrate')
        pubsub.subscribe(channel)
        for item in pubsub.listen():
            if not self.running or not item['type'] is 'message':
                break
            print item['channel'], ":", item['data']
            lock.acquire()
            self.last = self.time
            lock.release()

# start the background thread
lock = threading.Lock()
trigger = TriggerThread(r, config)
trigger.start()

channel = config.getint('input','channel')-1                         # one-offset in the ini file, zero-offset in the code
window  = round(config.getfloat('processing','window') * H.fSample)  # in samples

minval = None
maxval = None

t = 0

while True:
    time.sleep(config.getfloat('processing','window')/10)
    t += 1

    lock.acquire()
    if trigger.last == trigger.time:
        minval = None
        maxval = None
    trigger.time = t
    lock.release()

    H = ftc.getHeader()
    endsample = H.nSamples - 1
    if endsample<window:
        continue

    begsample = endsample - window + 1
    D = ftc.getData([begsample, endsample])
    D = D[:,channel]

    try:
        low_pass = config.getint('processing', 'low_pass')
    except:
        low_pass = None

    try:
        high_pass = config.getint('processing', 'high_pass')
    except:
        high_pass = None

    try:
        order = config.getint('general', 'order')
    except:
        order = None

    # FIXME the following has not been tested yet
    D = signal.butterworth(D, H.fSample, low_pass=low_pass, high_pass=high_pass, order=order)

    if minval is None:
        minval = np.min(D)

    if maxval is None:
        maxval = np.max(D)

    minval = min(minval,np.min(D))
    maxval = max(maxval,np.max(D))

    spread = np.max(D) - np.min(D)
    if spread > config.getfloat('processing','threshold')*(maxval-minval):
        val = 1
    else:
        val = 0

    print('spread ' + str(spread) +
          '\t  max_spread : ' + str(maxval-minval) +
          '\t  output ' + str(val))

    key = "%s.channel%d" % (config.get('output','prefix'), channel+1)
    r.publish(key,val)
