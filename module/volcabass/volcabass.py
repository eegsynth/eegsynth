#!/usr/bin/env python

import mido
import time
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import sys
import os

# the list of MIDI commands is the only aspect that is specific to the Volca Bass
# see http://media.aadl.org/files/catalog_guides/1444141_chart.pdf
# to implement MIDI output to another device, you can copy the code and update the following two lines
midi_name = ['slide_time', 'expression', 'octave', 'lfo_rate', 'lfo_int', 'vco_pitch1', 'vco_pitch2', 'vco_pitch3', 'attack', 'decay_release', 'cutoff_intensity', 'gate_time']
midi_code = [5, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'volcabass.ini'))

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('-------------------------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

port = mido.open_output(config.get('midi','device'))

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for name, cmd in zip(midi_name, midi_code):
        try:
            config.get('output', name)
            # commenting it out means that the control is to be skipped
            val = r.get(config.get('output', name))
            if val:
                val = int(val)
            else:
                val = config.getint('default', name)
            msg = mido.Message('control_change', control=cmd, value=int(val), channel=config.getint('general', 'channel'))
            print cmd, val
            port.send(msg)
        except:
            pass
