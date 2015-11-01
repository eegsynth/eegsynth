#!/usr/bin/python
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import serial

config = ConfigParser.ConfigParser()
config.read('devirtualizer.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)

s = serial.Serial(config.get('serial','device'), config.getint('serial','baudrate'), timeout=3.0)

while True:
    time.sleep(0.01)

    for chanindx in range(1, 8):
        chanstr = "control%d" % channel
        val = r.get(config.get('input', chanstr))
        if val:
            chanval = float(val)
        else:
            chanval = config.getfloat('default', chanstr)
        s.write('*c%dv%04d#' % {chanindx, chanval})

    for chanindx in range(1, 8):
        chanstr = "gate%d" % channel
        val = r.get(config.get('input', chanstr))
        if val:
            chanval = bool(val)
        else:
            chanval = config.getfloat('default', chanstr)
        s.write('*g%dv%d#' % {chanindx, chanval})
