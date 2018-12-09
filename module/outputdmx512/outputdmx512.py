#!/usr/bin/env python

# OutputDMX sends Redis data according to the DMX protocol
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
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

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

try:
    s = serial.Serial()
    s.port=patch.getstring('serial','device')
    s.baudrate=patch.getstring('serial','baudrate')
    s.bytesize=8
    s.parity='N'
    s.stopbits=2
    s.timeout=3.0
    # xonxoff=0
    # rtscts=0
    s.open()
    if debug>0:
        print "Connected to serial port"
except:
    print "Error: cannot connect to serial port"
    exit()

# give the device some time to initialize
time.sleep(2)

# determine the size of the universe
dmxsize = 16
chanlist,chanvals = map(list, zip(*config.items('input')))
for chanindx in range(1, 512):
    chanstr = "channel%03d" % chanindx
    if chanstr in chanlist:
        dmxsize = chanindx
if debug>0:
    print "universe size = %d" % dmxsize

# This is from https://www.enttec.com/docs/dmx_usb_pro_api_spec.pdf
#
# Reprogram Firmware Request (Label=1, no data)
# Program Flash Page Request (Label=2) -> Program Flash Page Reply (Label=2)
# Get Widget Parameters Request (Label=3) -> Get Widget Parameters Reply (Label=3)
# Set Widget Parameters Request (Label=4)
# Received DMX Packet (Label=5)
# Output Only Send DMX Packet Request (Label=6)
# Send RDM Packet Request (Label=7)
# Receive DMX On Change (Label=8)
# Received DMX Change Of State Packet (Label=9)
# Get Widget Serial Number Request (Label = 10, no data) -> Get Widget Serial Number Reply (Label = 10)
# Send RDM Discovery Request (Label=11)

# This is from http://agreeabledisagreements.blogspot.nl/2012/10/a-beginners-guide-to-dmx512-in-python.html
DMXOPEN=chr(126)    # char 126 is 7E in hex. It's used to start all DMX512 commands
DMXCLOSE=chr(231)   # char 231 is E7 in hex. It's used to close all DMX512 commands
DMXSENDPACKET=chr(6)+chr(1)+chr(2) 		# this is hard-coded for a universe size of 512 (plus one)
DMXINIT1=chr( 3)+chr(2)+chr(0)+chr(0)+chr(0)	# request widget params
DMXINIT2=chr(10)+chr(2)+chr(0)+chr(0)+chr(0)	# request widget serial

# Set up an array corresponding to the universe size plus one. The first element is the start code, which is 0.
# The first channel is not element 0, but element 1.
dmxdata=[chr(0)]*(dmxsize+1)

MSB=int(len(dmxdata)/256)
LSB=len(dmxdata)-MSB*256
DMXSENDPACKET=chr(6)+chr(LSB)+chr(MSB)

# this writes the initialization codes to the DMX
s.write(DMXOPEN+DMXINIT1+DMXCLOSE)
s.write(DMXOPEN+DMXINIT2+DMXCLOSE)

# senddmx accepts the 513 byte long data string to keep the state of all the channels
# senddmx writes to the serial port then returns the modified 513 byte array
def senddmx(data, chan, intensity):
    # because the spacer bit is [0], the channel number is the array item number
    # set the channel number to the proper value
    data[chan]=chr(intensity)
    # join turns the array data into a string we can send down the DMX
    sdata=''.join(data)
    # write the data to the serial port, this sends the data to your fixture
    s.write(DMXOPEN+DMXSENDPACKET+sdata+DMXCLOSE)
    # return the data with the new value in place
    return(data)

# keep a timer to send a packet every now and then
prevtime = time.time()

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        for chanindx in range(1, 512):
            chanstr = "channel%03d" % chanindx
            # this returns None when the channel is not present
            chanval = patch.getfloat('input', chanstr)

            if chanval==None:
                # the value is not present in Redis, skip it
                if debug>2:
                    print chanstr, 'not available'
                continue

            # the scale and offset options are channel specific
            scale  = patch.getfloat('scale', chanstr, default=255)
            offset = patch.getfloat('offset', chanstr, default=0)
            # apply the scale and offset
            chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
            # ensure that it is within limits
            chanval = EEGsynth.limit(chanval, lo=0, hi=255)
            chanval = int(chanval)

            if dmxdata[chanindx]!=chr(chanval):
                if debug>0:
                    print "DMX channel%03d" % chanindx, '=', chanval
                # update the DMX value for this channel
                dmxdata = senddmx(dmxdata,chanindx,chanval)
            elif (time.time()-prevtime)>1:
                # send a maintenance packet now and then
                dmxdata = senddmx(dmxdata,chanindx,chanval)
                prevtime = time.time()

except KeyboardInterrupt:
    if debug>0:
        print "closing..."
    sys.exit()
