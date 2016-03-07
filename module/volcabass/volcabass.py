#!/usr/bin/env python

import mido
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import threading
import time
import sys
import os

# the list of MIDI commands is the only aspect that is specific to the Volca Bass
# see http://media.aadl.org/files/catalog_guides/1444141_chart.pdf
control_name = ['slide_time', 'expression', 'octave', 'lfo_rate', 'lfo_int', 'vco_pitch1', 'vco_pitch2', 'vco_pitch3', 'attack', 'decay_release', 'cutoff_intensity', 'gate_time']
control_code = [5, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]
note_name = []
note_code = []

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
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
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

midichannel = config.getint('midi', 'channel')-1
mididevice  = config.get('midi', 'device')
outputport  = mido.open_output(mididevice)

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, note):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.note = note
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe(self.redischannel)
        for item in pubsub.listen():
            if not self.running:
                break
            else:
                print item['channel'], "=", item['data']
                msg = mido.Message('note_on', note=self.note, velocity=int(item['data']), channel=midichannel)
                outputport.send(msg)

# each of the notes that can be played is mapped onto a different trigger
trigger = []
for name, code in zip(note_name, note_code):
    try:
        # start the background thread that deals with the trigger
        this = TriggerThread(config.get('note', name), code)
        trigger.append(this)
        print name+' OK'
    except:
        # this happens when it is commented out in the ini file
        print name+' FAILED'

# start the thread for each of the notes
for thread in trigger:
    thread.start()

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for name, cmd in zip(control_name, control_code):
        # loop over the control values
        try:
            # it should be skipped when commented out in the ini file
            val = r.get(config.get('control', name))
            if val:
                val = int(val)
            else:
                val = config.getint('default', name)
            msg = mido.Message('control_change', control=cmd, value=int(val), channel=midichannel)
            # print cmd, val, name
            # print msg
            outputport.send(msg)
        except:
            pass
