#!/usr/bin/env python

# Outputartnet sends Redis data according to the artnet protocol
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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

import configparser
import argparse
import os
import redis
import serial
import sys
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth
import ArtNet

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug = patch.getint('general','debug')

# prepare the data for a single universe
address = [0, 0, patch.getint('artnet','universe')]
artnet = ArtNet.ArtNet(ip=patch.getstring('artnet','broadcast'), port=patch.getint('artnet','port'))

# blank out
dmxdata = [0] * 512
artnet.broadcastDMX(dmxdata,address)

# keep a timer to send a packet every now and then
prevtime = time.time()

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        # loop over the control values, these are 1-offset in the ini file
        for chanindx in range(1, 512):
            chanstr = "channel%03d" % chanindx
            # this returns None when the channel is not present
            chanval = patch.getfloat('input', chanstr)

            if chanval==None:
                # the value is not present in Redis, skip it
                if debug>2:
                    print(chanstr, 'not available')
                continue

            # the scale and offset options are channel specific
            scale  = patch.getfloat('scale', chanstr, default=255)
            offset = patch.getfloat('offset', chanstr, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            # ensure that it is within limits
            chanval = EEGsynth.limit(chanval, lo=0, hi=255)
            chanval = int(chanval)

            if dmxdata[chanindx-1]!=chanval:
                # update the DMX value for this channel
                dmxdata[chanindx-1] = chanval
                if debug>1:
                    print("DMX channel%03d" % chanindx, '=', chanval)
                artnet.broadcastDMX(dmxdata,address)
            elif (time.time()-prevtime)>1:
                # send a maintenance packet now and then
                artnet.broadcastDMX(dmxdata,address)
                prevtime = time.time()

except KeyboardInterrupt:
    # blank out
    if debug>0:
        print("closing...")
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
