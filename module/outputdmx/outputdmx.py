#!/usr/bin/env python

# OutputDMX sends DMX data using an Enttec DMX USB Pro, DMXKing ultraDMX Micro, or compatible interface
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
import sys
import time
import serial
import serial.tools.list_ports
from fuzzywuzzy import process

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
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth

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
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug = patch.getint('general', 'debug')

# get the specified serial device, or the one that is the closest match
serialdevice = patch.getstring('serial', 'device')
serialdevice = EEGsynth.trimquotes(serialdevice)
serialdevice = process.extractOne(serialdevice, [comport.device for comport in serial.tools.list_ports.comports()])[0] # select the closest match

try:
    s = serial.Serial(serialdevice, patch.getint('serial', 'baudrate'), timeout=3.0)
    monitor.info("Connected to serial port")
except:
    raise RuntimeError("cannot connect to serial port")

# determine the size of the universe
dmxsize = 0
chanlist, chanvals = list(map(list, list(zip(*config.items('input')))))
for chanindx in range(0, 512):
    chanstr = "channel%03d" % (chanindx + 1)
    if chanstr in chanlist:
        # the last channel determines the size
        dmxsize = chanindx

# my fixture won't work if the frame size is too small
dmxsize = max(dmxsize, 16)
module.info("universe size = %d" % dmxsize)

# make an empty frame
dmxframe = [0] * dmxsize

# See http://agreeabledisagreements.blogspot.nl/2012/10/a-beginners-guide-to-dmx512-in-python.html
# See https://www.enttec.com/docs/dmx_usb_pro_api_spec.pdf

START_VAL = 0x7E
END_VAL = 0xE7
TX_DMX_PACKET = 0x06
FRAME_PAD = 0x00

def sendframe():
    packet = [
        START_VAL,
        TX_DMX_PACKET,
        ((len(dmxframe) + 1) >> 0) & 0xFF,
        ((len(dmxframe) + 1) >> 8) & 0xFF,
        FRAME_PAD
    ]
    packet.extend(dmxframe)
    packet.append(END_VAL)
    monitor.debug(packet)
    packet = map(chr, packet)
    s.write(''.join(packet))

# keep a timer to send a packet every now and then
prevtime = time.time()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

        update = False
        for chanindx in range(0, dmxsize):
            chanstr = "channel%03d" % (chanindx + 1)
            # this returns None when the channel is not present
            chanval = patch.getfloat('input', chanstr)

            if chanval == None:
                # the value is not present in Redis, skip it
                continue

            # the scale and offset options are channel specific
            scale = patch.getfloat('scale', chanstr, default=255)
            offset = patch.getfloat('offset', chanstr, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            # ensure that it is within limits
            chanval = EEGsynth.limit(chanval, lo=0, hi=255)
            chanval = int(chanval)

            # only update if the value has changed
            if dmxframe[chanindx] != chanval:
                monitor.info("DMX channel%03d = %g" % (chanindx, chanval))
                dmxframe[chanindx] = chanval
                update = True

        if update:
            sendframe()
            prevtime = time.time()

        elif (time.time() - prevtime) > 0.5:
            # send a maintenance frame every 0.5 seconds
            sendframe()
            prevtime = time.time()


except KeyboardInterrupt:
    monitor.success("closing...")
    # blank out everything
    dmxframe = [0] * 512
    sendframe()
    sys.exit()
