#!/usr/bin/env python

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import mido
import os
import redis
import sys
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('------ INPUT ------')
for port in mido.get_input_names():
  print(port)
print('-------------------------')

try:
    inputport  = mido.open_input(config.get('midi', 'device'))
    if debug>0:
        print "Connected to MIDI input"
except:
    print "Error: cannot connect to MIDI input"
    exit()

while True:
    time.sleep(config.getfloat('general','delay'))

    for msg in inputport.iter_pending():

        if debug>0:
            print msg

        if hasattr(msg, "control"):
            # prefix.control000=value
            key = "{}.control{:0>3d}".format(config.get('output', 'prefix'), msg.control)
            val = msg.value
            r.set(key, val)

        elif hasattr(msg, "note"):
            # prefix.noteXXX=value
            key = "{}.note{:0>3d}".format(config.get('output','prefix'), msg.note)
            r.set(key,msg.value)          # send it as control value
            r.publish(key,msg.value)      # send it as trigger
            # prefix.note=note
            key = "{}.note".format(config.get('output','prefix'))
            r.set(key,msg.note)          # send it as control value
            r.publish(key,msg.note)      # send it as trigger
