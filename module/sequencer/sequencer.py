#!/usr/bin/env python

import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import argparse
import math
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
    r = redis.StrictRedis(host=config.get('redis','hostname'),port=config.getint('redis','port'),db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

pattern = EEGsynth.getint('input','pattern', config, r, default=0)
previous = pattern

try:
  sequence = config.get('sequence',"pattern{:d}".format(pattern))
except:
  sequence = '0'

print pattern, sequence

try:
    while True:

        for note in sequence.split():
            note = int(note)

            # this will return empty if not available
            pattern = EEGsynth.getint('input','pattern', config, r, default=0)

            if pattern!=previous:
                # get the corresponding sequence
                pattern = EEGsynth.getint('input','pattern', config, r, default=0)
                try:
                  sequence = config.get('sequence',"pattern{:d}".format(pattern))
                except:
                  sequence = '0'
                # immediately start playing the new sequence
                previous = pattern
                print 'break'
                break

            # use a default rate of 90 bpm
            rate = EEGsynth.getfloat('input','rate', config, r)
            if rate is None:
                rate = 90

            # use a default transposition of 48
            transpose = EEGsynth.getint('input','transpose', config, r)
            if transpose is None:
                transpose = 48

            # assume that the rate value is between 0 and 127, map it exponentially from 20 to 2000
            # it should not get too low, otherwise the code with the sleep below becomes unresponsive
            rate = 20*math.exp(rate*math.log(100)/127)

            if debug>0:
                print pattern, rate, transpose, note

            key = "{}.note".format(config.get('output','prefix'))
            val = note + transpose

            r.set(key,val)      # send it as control value: prefix.channel000.note=note
            r.publish(key,val)  # send it as trigger: prefix.channel000.note=note

            time.sleep(60/rate)

except KeyboardInterrupt:
    try:
        print "Disabling last note"
        r.set(key,0)
        r.publish(key,0)
    except:
        pass
