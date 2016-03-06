#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import multiprocessing
import threading

import numpy as np

from nilearn import signal

# eegsynth/lib contains shared modules
sys.path.insert(0, '../../lib')
import FieldTrip

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'emg.ini'))

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

class TriggerThread(threading.Thread):
    def __init__(self, r, config):
        threading.Thread.__init__(self)
        self.r = r
        self.config = config
        self.stopped = False
        lock.acquire()
        self.time = 0
        self.last = 0
        lock.release()
    def stop_thread(self):
        self.stopped = True
    def run(self):
        pubsub = self.r.pubsub()
        channel = self.config.get('input','calibrate')
        pubsub.subscribe(channel)
        for item in pubsub.listen():
            if self.stopped:
                break
            else:
                print item['channel'], ":", item['data']
                lock.acquire()
                self.last = self.time
                lock.release()

# start the background thread
lock = threading.Lock()
trigger = TriggerThread(r, config)
trigger.start()

ftc = FieldTrip.Client()

H = None
while H is None:
    print 'Trying to connect to buffer on %s:%i ...' % (config.get('fieldtrip','hostname'), config.getint('fieldtrip','port'))
    ftc.connect(config.get('fieldtrip','hostname'), config.getint('fieldtrip','port'))
    print '\nConnected - trying to read header...'
    H = ftc.getHeader()

print H
print H.labels

blocksize = round(config.getfloat('general','blocksize') * H.fSample)
print blocksize

hwchanindx = []
hwdataindx = []
for chanindx in range(0, 9):
    try:
        chanstr = "channel%d" % (chanindx+1)
        hwchanindx.append(config.getint('input', chanstr)-1)
        hwdataindx.append(chanindx+1)

    except:
        pass

print hwchanindx,hwdataindx
minval = None
maxval = None

t = 0

while True:
    time.sleep(config.getfloat('general','blocksize')/10)
    t += 1

    lock.acquire()
    if trigger.last == trigger.time:
        minval = None
        maxval = None
    trigger.time = t
    lock.release()

    H = ftc.getHeader()
    endsample = H.nSamples - 1
    if endsample<blocksize:
        continue

    begsample = endsample-blocksize+1
    D = ftc.getData([begsample, endsample])


    D = D[:,hwchanindx]

    try:
        low_pass = config.getint('general', 'low_pass')
    except:
        low_pass = None


    try:
        high_pass = config.getint('general', 'high_pass')
    except:
        high_pass = None




    D_filt = signal.butterworth(D,H.fSample, low_pass=low_pass, high_pass=high_pass, order=config.getint('general', 'order'))




    rms = []
    for i in range(0,len(hwchanindx)):
        rms.append(0)

    #print len(rms)

    for i,chanvec in enumerate(D_filt.transpose()):
        for chanval in chanvec:
            rms[i] += chanval*chanval

    if minval is None:
        minval = rms

    if maxval is None:
        maxval = rms

    minval = [min(a,b) for (a,b) in zip(rms,minval)]
    maxval = [max(a,b) for (a,b) in zip(rms,maxval)]



    for i,val in enumerate(rms):
        if maxval[i]==minval[i]:
            rms[i] = 0
        else:
            rms[i] = (rms[i]-minval[i])/(maxval[i]-minval[i])

    print rms

    for i,val in enumerate(rms):
        key = "%s.channel%d" % (config.get('output','prefix'), hwdataindx[i])
        # send it as control value: prefix.channelX=val
        r.set(key,int(127*val))
