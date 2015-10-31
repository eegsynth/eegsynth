#!/usr/bin/python
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import serial

config = ConfigParser.ConfigParser()
config.read('devirtualizer.ini')

r = redis.StrictRedis(host=config.get('input','hostname'), port=config.getint('input','port'), db=0)
r.set('foo', 'bar')
r.get('foo')

s = serial.Serial(config.get('output','device'), config.getint('output','baudrate'), timeout=3.0)

while True:
    time.sleep(0.01)

    for chanindx in range(1, 4):
        chanstr = "output%d" % channel
        val = r.get(config.get('input', chanstr))
        if val:
            chanval = float(val)
        else:
            chanval = config.getfloat('default', chanstr)
        s.write('*c%dv%04d#' % {chanindx, chanval})
