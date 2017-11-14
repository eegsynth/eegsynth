#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import os
import redis
import serial
import sys
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
import ArtNet

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

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

# prepare the data for a single universe
address = [0, 0, config.getint('artnet','universe')]
artnet = ArtNet.ArtNet(ip=config.get('artnet','broadcast'), port=config.getint('artnet','port'))

# blank out
dmxdata = [0] * 512
artnet.broadcastDMX(dmxdata,address)

# keep a timer to send a packet every now and then
prevtime = time.time()

try:
    while True:
        time.sleep(config.getfloat('general', 'delay'))

        for chanindx in range(1, 256):
            chanstr = "channel%03d" % chanindx

            try:
                chanval = EEGsynth.getfloat('input', chanstr, config, r)
            except:
                # the channel is not configured in the ini file, skip it
                continue

            if chanval==None:
                # the value is not present in redis, skip it
                continue

            if EEGsynth.getint('compressor_expander', 'enable', config, r):
                # the compressor applies to all channels and must exist as float or redis key
                lo = EEGsynth.getfloat('compressor_expander', 'lo', config, r)
                hi = EEGsynth.getfloat('compressor_expander', 'hi', config, r)
                if lo is None or hi is None:
                    if debug>1:
                        print "cannot apply compressor/expander"
                else:
                    # apply the compressor/expander
                    chanval = EEGsynth.compress(chanval, lo, hi)

            # the scale option is channel specific
            scale = EEGsynth.getfloat('scale', chanstr, config, r, default=1)
            # the offset option is channel specific
            offset = EEGsynth.getfloat('offset', chanstr, config, r, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            chanval = int(chanval)

            if dmxdata[chanindx-1]!=chanval:
                # update the DMX value for this channel
                dmxdata[chanindx-1] = chanval
                if debug>1:
                    print "DMX channel%03d" % chanindx, '=', chanval
                artnet.broadcastDMX(dmxdata,address)
            elif (time.time()-prevtime)>1:
                # send a maintenance packet now and then
                artnet.broadcastDMX(dmxdata,address)
                prevtime = time.time()

except KeyboardInterrupt:
    # blank out
    if debug>0:
        print "closing..."
    dmxdata = [0] * 512
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxdata,address)
    time.sleep(0.1) # this seems to take some time
    artnet.close()
    sys.exit()
