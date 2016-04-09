#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import mido
import serial
import threading
import time
import sys
import os
import numpy as np

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

serialport = None
def initialize_serial():
    try:
        serialport = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)
    except:
        print "Error: cannot connect to serial output"
        exit()
    return serialport

midiport = None
def initialize_midi():
    midiport = EEGsynth.midiwrapper(config)
    midiport.open_output()
    return midiport

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.enabled = False
        self.rate = 60
    def setRate(self, rate):
        lock.acquire()
        self.rate = rate
        lock.release()
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def stop(self):
        self.running = False
    def run(self):
        msg = mido.Message('clock')
        slip = 0
        if debug>0:
            print msg
        while self.running:
            if not self.enabled:
                time.sleep(config.getfloat('general', 'delay'))
            else:
                now = time.time()
                delay = 60/self.rate      # the rate is in bpm
                delay -= slip             # correct for the slip from the previous iteration
                jiffy = delay/(24)
                for iteration in range(24):
                    midiport.send(msg)
                    time.sleep(jiffy)
                # the time used in this loop will be slightly different than desired
                slip = time.time() - now - delay

def find_nearest_idx(array,value):
    # find the index of the array element that is the nearest to the value
    idx = (np.abs(np.asarray(array)-value)).argmin()
    return idx

multiplier_mid = [   10,    30,    50,   70,   90,   110,   130 ] # lookup table
multiplier_val = [ 1./4,  1./3,  1./1,    1,    2,     3,     4 ] # actual value

slip            = 0
tick            = 0
adjust_offset   = 0
previous_offset = 0
pulselength = config.getfloat('general','pulselength')

# this is how it will appear in REDIS
key = "%s.%s" % (config.get('output','prefix'), config.get('input','rate'))

# these will only be started when needed
init_midi   = False
init_serial = False

previous_use_midi = None
previous_use_serial = None

try:
    # start the thread that synchronizes over MIDI
    midisync = TriggerThread()
    midisync.start()

    while True:
        # measure the time to correct for the slip
        now = time.time()

        use_serial = EEGsynth.getint('general', 'serial', config, r, default=0)
        use_midi   = EEGsynth.getint('general', 'midi', config, r, default=0)
        use_redis  = EEGsynth.getint('general', 'redis', config, r, default=0)

        if previous_use_serial is None:
            previous_use_serial = not(use_serial);

        if previous_use_midi is None:
            previous_use_midi = not(use_midi);

        if use_serial and not init_serial:
            # this might not be running at the start
            serialport = initialize_serial()
            init_serial = True

        if use_midi and not init_midi:
            # this might not be running at the start
            midiport = initialize_midi()
            init_midi = True

        if use_midi and not previous_use_midi:
            midisync.enable()
            previous_use_midi = True
        elif not use_midi and previous_use_midi:
            midisync.disable()
            previous_use_midi = False

        rate = EEGsynth.getfloat('input', 'rate', config, r)
        if rate is None:
            time.sleep(config.getfloat('general', 'delay'))
            continue

        offset = EEGsynth.getfloat('input', 'offset', config, r, default=64)
        # the offset value from 0-127 gets scaled to a value from -1 to +1 seconds
        offset = (offset-64)/(127/2)

        multiplier = EEGsynth.getfloat('input', 'multiplier', config, r, default=1)
        # the multiplier value from 0-127 gets scaled to a value from 1/4 to 16/4
        idx = find_nearest_idx(multiplier_mid, multiplier)
        multiplier = multiplier_val[idx]

        # update the thread that synchronizes over MIDI
        midisync.setRate(rate*multiplier)

        try:
       	    delay = 60/(rate*multiplier)
        except:
            delay = 1
        delay = max(delay, pulselength) # cannot be shorter than the pulse length

        adjust_offset  += offset - previous_offset  # correct for the user specified offset
        previous_offset = offset

        if debug>0:
            print use_redis, use_midi, use_serial

        if debug>0:
            print rate, offset, multiplier, adjust_offset, slip

        if (adjust_offset-slip)<0:
            if (delay-pulselength+adjust_offset-slip)<0:
                if debug>0:
                    print "skip"
                # don't send a pulse and don't sleep at all
                adjust_offset += (delay-pulselength)
            else:
                if debug>0:
                    print "tick", tick
                    tick+=1
                if use_serial:
                    serialport.write('*g1v1#')
                if use_redis:
                    r.publish(key,127)      # send it as trigger
                # sleep for the duration of the pulse
                time.sleep(pulselength)
                if use_serial:
                    serialport.write('*g1v0#')
                if use_redis:
                    r.publish(key,0)        # send it as trigger
                # sleep a reduced amount
                time.sleep(delay-pulselength+adjust_offset-slip)
                adjust_offset = 0
        else:
            if debug>0:
                print "tick", tick
                tick+=1
            if use_serial:
                serialport.write('*g1v1#')
            if use_redis:
                r.publish(key,127)          # send it as trigger
            # sleep for the duration of the pulse
            time.sleep(pulselength)
            if use_serial:
                serialport.write('*g1v0#')
            if use_redis:
                r.publish(key,0)            # send it as trigger
            # sleep an increased amount
            time.sleep(delay-pulselength+adjust_offset-slip)
            adjust_offset = 0

        # the time used in this loop will be slightly different than desired
        # this will be corrected in the next iteration
        slip += time.time() - now - delay

except KeyboardInterrupt:
    print "Closing threads"
    midisync.stop()
    midisync.join()
    sys.exit()
