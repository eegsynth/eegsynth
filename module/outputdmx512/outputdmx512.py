#!/usr/bin/env python

import sys
import os
import time
import redis
import serial
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API

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

# this is from http://agreeabledisagreements.blogspot.nl/2012/10/a-beginners-guide-to-dmx512-in-python.html
DMXOPEN=chr(126)    # char 126 is 7E in hex. It's used to start all DMX512 commands
DMXCLOSE=chr(231)   # char 231 is E7 in hex. It's used to close all DMX512 commands
DMXINTENSITY=chr(6)+chr(1)+chr(2)
DMXINIT1=chr(03)+chr(02)+chr(0)+chr(0)+chr(0)
DMXINIT2=chr(10)+chr(02)+chr(0)+chr(0)+chr(0)

# this writes the initialization codes to the DMX
s.write(DMXOPEN+DMXINIT1+DMXCLOSE)
s.write(DMXOPEN+DMXINIT2+DMXCLOSE)

# set up an array of 513 bytes, the first item in the array ( dmxdata[0] ) is the previously
# mentioned spacer byte following the header. This makes the array math more obvious.
dmxdata=[chr(0)]*513

# senddmx accepts the 513 byte long data string to keep the state of all the channels
# senddmx writes to the serial port then returns the modified 513 byte array
def senddmx(data, chan, intensity):
    # because the spacer bit is [0], the channel number is the array item number
    # set the channel number to the proper value
    data[chan]=chr(intensity)
    # join turns the array data into a string we can send down the DMX
    sdata=''.join(data)
    # write the data to the serial port, this sends the data to your fixture
    s.write(DMXOPEN+DMXINTENSITY+sdata+DMXCLOSE)
    # return the data with the new value in place
    return(data)

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
        chanval=int(chanval)

        if dmxdata[chanindx]!=chr(chanval):
            if debug>0:
                print "DMX channel%03d" % chanindx, '=', chanval
            # update the DMX value for this channel
            dmxdata = senddmx(dmxdata,chanindx,chanval)
