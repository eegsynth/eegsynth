#!/usr/bin/env python

import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
# import serial
import sys
import os

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'pulsegenerator.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# send it to redis rather than sending it directly to the serial interface
# s = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)

previous_offset=0
delay=60
pulselength = config.getfloat('general','pulselength')
key=config.get('output','channel')

while True:
    val = r.get(config.get('input', 'channel'))
    if val:
        cv_rate = float(val)
    else:
        cv_rate = config.getfloat('default','rate')

    val = r.get(config.get('input', 'offset'))
    if val:
        cv_offset = float(val)
    else:
        cv_offset = config.getfloat('default','offset')

    val = r.get(config.get('input', 'multiplier'))
    if val:
        cv_multiplier = float(val)
    else:
        cv_multiplier = config.getfloat('default','multiplier')

    adjust_offset = previous_offset - cv_offset
    try:
    	delay = 60/(cv_rate*cv_multiplier) - adjust_offset
    except:
        pass

    print 'delay in seconds =', delay

    # send it to redis rather than sending it directly to the serial interface
    # s.write('*g1v1#')
    # s.write('*g2v1#')
    val = 127               # set the note on
    r.publish(key,val)      # send it as trigger
    if pulselength<(delay/2):
        time.sleep(pulselength)
    else:
        # the desired duration between beats is too short, split the delay in half
        time.sleep(delay/2)

    # send it to redis rather than sending it directly to the serial interface
    # s.write('*g1v0#')
    # s.write('*g2v0#')
    val = 0                 # set the note off
    r.publish(key,val)      # send it as trigger
    if pulselength<(delay/2):
        time.sleep(delay-pulselength)
    else:
        # the desired duration between beats is too short, split the delay in half
        time.sleep(delay/2)
