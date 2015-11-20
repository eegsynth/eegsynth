#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis

config = ConfigParser.ConfigParser()
config.read('keyboard.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)

mido.get_input_names()

port = mido.open_input(config.get('midi','device'))

while True:
    for msg in port.iter_pending():
        # FIXME here it should decide on a key-value pair and send that to redis
        print(msg)
