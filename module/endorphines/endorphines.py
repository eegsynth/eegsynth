#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os
import threading
import mido

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general', 'debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

outputport = EEGsynth.midiwrapper(config)
outputport.open_output()

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
                    lock.acquire()
                    outputport.send(msg)
                    lock.release()
                    # keep it at the present value for a minimal amount of time
                    time.sleep(config.getfloat('general','pulselength'))

# each of the gates that can be triggered is mapped onto a different message
gate = []
for channel in range(0, 16):
    # channels are one-offset in the ini file, zero-offset in the code
    name = 'channel{}'.format(channel+1)
    if config.has_option('gate', name):
        # start the background thread that deals with this channel
        this = TriggerThread(config.get('gate', name), channel)
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
        time.sleep(config.getfloat('general', 'delay'))

        # loop over the control values
        for channel in range(0, 16):
            # channels are one-offset in the ini file, zero-offset in the code
            name = 'channel{}'.format(channel+1)
            val = EEGsynth.getfloat('control', name, config, r)
            if val is None:
                if debug>2:
                    print name, 'not available'
                continue

            if EEGsynth.getfloat('limiter_compressor', 'enable', config, r):
                # the limiter/compressor applies to all channels and must exist as float or redis key
                lo = EEGsynth.getfloat('limiter_compressor', 'lo', config, r)
                hi = EEGsynth.getfloat('limiter_compressor', 'hi', config, r)
                if lo is None or hi is None:
                    if debug>1:
                        print "cannot apply limiter/compressor"
                else:
                    # apply the limiter/compressor
                    val = EEGsynth.limiter(val, lo, hi)

            # the scale option is channel specific
            scale = EEGsynth.getfloat('scale', name, config, r, default=1)
            # the offset option is channel specific
            offset = EEGsynth.getfloat('offset', name, config, r, default=0)

            # apply the scale and offset
            val = EEGsynth.rescale(val, slope=scale, offset=offset)

            # ensure that it is within limits
            val = EEGsynth.clip(val, lower=-8192, upper=8191)

            if debug>0:
                print name, val

            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            previous_val[name] = val

            # midi channels in the inifile are 1-16, in the code 0-15
            midichannel = channel
            msg = mido.Message('pitchwheel', pitch=int(val), channel=midichannel)
            if debug>1:
                print msg
            outputport.send(msg)

except KeyboardInterrupt:
    print 'Closing threads'
    for thread in gate:
        thread.stop()
    r.publish('ENDORPHINES_UNBLOCK', 1)
    for thread in gate:
        thread.join()
    sys.exit()
