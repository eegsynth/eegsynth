#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis

config = ConfigParser.ConfigParser()
config.read('launchcontrol.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('-------------------------')
for port in mido.get_input_names():
  print(port)
print('-------------------------')

port = mido.open_input(config.get('midi','device'))

while True:
    for msg in port.iter_pending():
        print(msg)
        if hasattr(msg, "control"):
            # prefix.channel000.control000=value
            key = "{}.channel{:0>2d}.control{:0>3d}".format(config.get('output', 'prefix'), msg.channel, msg.control)
            val = msg.value
            r.set(key, val)
        elif hasattr(msg, "note"):
            if config.get('output','action')=="release" and msg.velocity>0:
                pass
            elif config.get('output','action')=="press" and msg.velocity==0:
                pass
            else:
                # send it as control value: prefix.channel000.note=note
                key = "{}.channel{:0>2d}.note".format(config.get('output','prefix'),msg.channel)
                val = msg.note
                r.set(key,val)
                # send it as trigger: prefix.channel000.note=note
                key = "{}.channel{:0>2d}.note".format(config.get('output','prefix'),msg.channel)
                val = msg.note
                r.publish(key,val)
    time.sleep(0.001)
