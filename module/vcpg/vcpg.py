#!/usr/bin/python
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import serial

config = ConfigParser.ConfigParser()
config.read('vcpg.ini')

for section in config.sections():
    print section
    for option in config.options(section):
        print " ", option, "=", config.get(section, option)


r = redis.StrictRedis(host=config.get('input','hostname'), port=int(config.get('input','port')), db=0)
r.set('foo', 'bar')
r.get('foo')


s = serial.Serial(onfig.get('output','device'), int(config.get('output','baudrate')), timeout=3.0)

while True:
    s.write("\r\nSay something:")
    rcv = s.read(10)
    s.write("\r\nYou sent:" + repr(rcv))


print "Start : %s" % time.ctime()
time.sleep( 5 )
print "End : %s" % time.ctime()
