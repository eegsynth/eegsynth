#!/usr/bin/python
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import serial

config = ConfigParser.ConfigParser()
config.read('pulsegenerator.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
r.set('foo', 'bar')
r.get('foo')

s = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)

previous_offset=0

while True:
    val = r.get(config.get('input', 'rate'))
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
    delay = 60/(cv_rate*cv_multiplier) - adjust_offset

    s.write('*g1v1#')
    time.sleep( delay/2 )
    s.write('*g1v0#')
    time.sleep( delay/2 )
