#!/usr/bin/env python

import math
import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import redis
import time
import sys
import os

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'sequencer.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'),port=config.getint('redis','port'),db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

pattern = r.get(config.get('input','pattern'))
if pattern:
    pattern = int(pattern)
else:
    pattern = config.getint('default','pattern')
previous = pattern

# get the corresponding pattern
sequence = config.get('sequence',"pattern{:0>3d}".format(pattern))

while True:

    for note in sequence.split():
        # this will return empty if not available
        new = r.get(config.get('input','pattern'))
        if new:
            new = int(new)
        else:
            new = config.getint('default','pattern')

        if pattern!=new:
            pattern = new
            try:
              sequence = config.get('sequence',"pattern{:0>3d}".format(pattern))
            except:
              pass
            # immediately start playing the new sequence
            break

        rate = r.get(config.get('input','rate'))
        if rate:
            rate = float(rate)
        else:
            rate = config.getfloat('default','rate')
        # assume that value is between 0 and 127, map exponentially from 20 to 2000
        # it should not get too low, otherwise the code with the sleep below becomes unresponsive
        rate = 20*math.exp(rate*math.log(100)/127)

        offset = r.get(config.get('input','offset'))
        if offset:
            offset = int(offset)
        else:
            offset = config.getint('default','offset')

        note = int(note)

        print(pattern, int(rate), offset, note)

        key = "{}.note".format(config.get('output','prefix'))
        val = note+offset
        # send it as control value: prefix.channel000.note=note
        r.set(key,val)
        # send it as trigger: prefix.channel000.note=note
        r.publish(key,val)

        time.sleep(60/rate)
