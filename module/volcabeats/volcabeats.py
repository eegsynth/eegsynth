#!/usr/bin/env python

import mido
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import threading
import time
import sys
import os

# the list of MIDI commands is the only aspect that is specific to the Volca Beats
# see http://media.aadl.org/files/catalog_guides/1445131_chart.pdf
# to implement MIDI output to another device, you can copy the code and update the following two lines
midi_name = ['kick_level', 'snare_level', 'lo_tom_level', 'hi_tom_level', 'closed_hat_level', 'open_hat_level', 'clap_level', 'claves_level', 'agogo_level', 'crash_level', 'clap_speed', 'claves_speed', 'agogo_speed', 'crash_speed', 'stutter_time', 'stutter_depth', 'tom_decay', 'closed_hat_decay', 'open_hat_decay', 'hat_gra    in']
midi_code = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
installed_folder = os.path.split(basis)[0]

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'volcabeats.ini'))

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

class TriggerThread(threading.Thread):
    def __init__(self, r, midichannel, redischannel, note):
        threading.Thread.__init__(self)
        self.r = r
        self.channel = redischannel
        self.note = note
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        print 'run'
        pubsub = self.r.pubsub()
        pubsub.subscribe(self.redischannel)
        for item in pubsub.listen():
            if not self.running:
                break
            else:
                print item['channel'], ":", item['data']
                msg = mido.Message('note_on', note=self.note, velocity=127, channel=self.midichannel)
                port.send(msg)

note_name = ['kick', 'snare', 'lo_tom', 'hi_tom', 'cl_hat', 'op_hat', 'clap']
note_code = [36, 38, 43, 50, 42, 46, 39]

midichannel = config.getint('general', 'channel')

# start the background thread that deals with triggers
trigger = TriggerThread(r, midichannel, config.get('note', note_name[1]), note_code[1])
trigger.start()

while True:
    time.sleep(config.getfloat('general', 'delay'))

    for name, cmd in zip(midi_name, midi_code):
        # loop over the control values
        try:
            rediscontrol = config.get('control', name)
            # it should be skipped when commented out in the ini file
            val = r.get(control)
            if val:
                val = int(val)
            else:
                val = config.getint('default', name)
            msg = mido.Message('control_change', control=cmd, value=int(val), channel=midichannel)
            # print cmd, val, name
            print msg
            port.send(msg)
        except:
            pass
