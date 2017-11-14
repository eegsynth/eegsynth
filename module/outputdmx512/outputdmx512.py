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

try:
    s = serial.Serial()
    s.port=config.get('serial','device')
    s.baudrate=config.get('serial','baudrate')
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
        time.sleep(config.getfloat('general', 'delay'))

        for chanindx in range(1, 512):
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
