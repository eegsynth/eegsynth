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
import EEGsynth

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'brain.ini'))

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
        pubsub.subscribe('BRAIN_UNBLOCK')  # this message unblocks the redis listen command
        for item in pubsub.listen():
            if not self.running:
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

ftc = FieldTrip.Client()

H = None
while H is None:
    print 'Trying to connect to buffer on %s:%i ...' % (config.get('fieldtrip','hostname'), config.getint('fieldtrip','port'))
    ftc.connect(config.get('fieldtrip','hostname'), config.getint('fieldtrip','port'))
    print '\nConnected - trying to read header...'
    H = ftc.getHeader()

if debug>1:
    print H
    print H.labels

channel_items = config.items('input')
channame = []
chanindx = []
for item in channel_items:
    # channel numbers are one-offset in the ini file, zero-offset in the code
    channame.append(item[0])
    chanindx.append(config.getint('channel', item[0])-1)

if debug>0:
    print channame, chanindx

window = int(round(config.getfloat('processing','window') * H.fSample))
minval = None
maxval = None
freeze = False

taper = np.hanning(window)
frequency = np.fft.rfftfreq(window, 1.0/H.fSample)

if debug>0:
    print 'taper     = ', taper
    print 'frequency = ', frequency

try:
    while True:
        time.sleep(config.getfloat('general','delay'))

        band_items = config.items('band')
        bandname = []
        bandlo   = []
        bandhi   = []
        for item in band_items:
            # channel numbers are one-offset in the ini file, zero-offset in the code
            lohi = EEGsynth.getfloat('band', item[0], config, r, multiple=True)
            print item[0], lohi
            # lohi = config.get('band', item[0]).split("-")
            bandname.append(item[0])
            bandlo.append(lohi[0])
            bandhi.append(lohi[1])
        if debug>0:
            print bandname, bandlo, bandhi

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

        power = []
        for chan in channame:
            for band in bandname:
                power.append(0)

        D = D[:, chanindx]
        M = D.mean(0)

        # subtract the channel mean and apply the taper to each sample
        for chan in range(D.shape[1]):
            for sample in range(D.shape[0]):
                D[sample,chan] -= M[chan]
                D[sample,chan] *= taper[sample]

        # compute the FFT over the sample direction
        F = np.fft.rfft(D,axis=0)

        i = 0
        for chan in range(F.shape[1]):
            for lo,hi in zip(bandlo,bandhi):
                power[i] = 0
                for sample in range(len(frequency)):
                    if frequency[sample]>=lo and frequency[sample]<=hi:
                        power[i] += abs(F[sample,chan]*F[sample,chan])
                i+=1

        if debug>1:
            print power

        if minval is None:
            minval = power
        if maxval is None:
            maxval = power

        if not freeze:
            # update the min/max value for the automatic gain control
            minval = [min(a,b) for (a,b) in zip(power,minval)]
            maxval = [max(a,b) for (a,b) in zip(power,maxval)]

        # apply the gain control
        for i,val in enumerate(power):
            if maxval[i]==minval[i]:
                power[i] = 0
            else:
                power[i] = (power[i]-minval[i])/(maxval[i]-minval[i])

        i = 0
        for chan in channame:
            for band in bandname:
                # send the control value prefix.channel.band=value
                key = "%s.%s.%s" % (config.get('output','prefix'), chan, band)
                val = int(127.0*power[i])
                r.set(key,val)
                i+=1

except KeyboardInterrupt:
    print "Closing threads"
    trigger.stop()
    r.publish('BRAIN_UNBLOCK', 1)
    trigger.join()
    sys.exit()
