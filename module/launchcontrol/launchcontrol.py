#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis

config = ConfigParser.ConfigParser()
config.read('launchcontrol.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)

# this is only for debugging
mido.get_input_names()

port = mido.open_input(config.get('midi','device'))

while True:
    for msg in port.iter_pending():
	if hasattr(msg, "control"):
		# prefix.channel000.control000=value
		key = "{}.channel{:0>2d}.control{:0>3d}".format(config.get('output', 'prefix'), msg.channel, msg.control)
		val = msg.value
		r.set(key, val)
	elif hasattr(msg, "note"):
		# prefix.channel000.note000=velocity
		key = "{}.channel{:0>2d}.note{:0>3d}".format(config.get('output', 'prefix'), msg.channel, msg.note)
		val = msg.velocity
		r.publish(key, val)
        print(msg)
