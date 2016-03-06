#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'keyboard.ini'))

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
        if hasattr(msg,"note"):
            print(msg)
            if config.get('output','action')=="release" and msg.velocity>0:
                pass
            elif config.get('output','action')=="press" and msg.velocity==0:
                pass
            else:
                # prefix.note=note
                key = "{}.note".format(config.get('output','prefix'))
                val = msg.note
                r.set(key,val)          # send it as control value
                r.publish(key,val)      # send it as trigger
                # prefix.noteXXX=velocity
                key = "{}.note{:0>3d}".format(config.get('output','prefix'), msg.note)
                val = msg.velocity
                r.set(key,val)          # send it as control value
                r.publish(key,val)      # send it as trigger
        elif hasattr(msg,"control"):
            # ignore these
            pass
        elif hasattr(msg,"time"):
            # ignore these
            pass
    time.sleep(0.001)
