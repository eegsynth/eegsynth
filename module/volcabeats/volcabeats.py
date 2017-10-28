#!/usr/bin/env python

import mido
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import threading
import time
import sys
import os
import argparse

# the list of MIDI commands is the only aspect that is specific to the Volca Beats
# see http://media.aadl.org/files/catalog_guides/1445131_chart.pdf
control_name = ['kick_level', 'snare_level', 'lo_tom_level', 'hi_tom_level', 'closed_hat_level', 'open_hat_level', 'clap_level', 'claves_level', 'agogo_level', 'crash_level', 'clap_speed', 'claves_speed', 'agogo_speed', 'crash_speed', 'stutter_time', 'stutter_depth', 'tom_decay', 'closed_hat_decay', 'open_hat_decay', 'hat_gra    in']
control_code = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
note_name = ['kick', 'snare', 'lo_tom', 'hi_tom', 'closed_hat', 'open_hat', 'clap']
note_code = [36, 38, 43, 50, 42, 46, 39]

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
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# this is only for debugging
print('------ OUTPUT ------')
for port in mido.get_output_names():
  print(port)
print('-------------------------')

midichannel = config.getint('midi', 'channel')-1  # channel 1-16 get mapped to 0-15
outputport = EEGsynth.midiwrapper(config)
outputport.open_output()

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

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
        pubsub.subscribe('VOLCABEATS_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)     # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    if debug>1:
                        print item['channel'], "=", item['data']
                    msg = mido.Message('note_on', note=self.note, velocity=int(item['data']), channel=midichannel)
                    lock.acquire()
                    outputport.send(msg)
                    lock.release()

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

# control values are only relevant when different from the previous value
previous_val = {}
for name in control_name:
    previous_val[name] = None

try:
    while True:
        time.sleep(config.getfloat('general', 'delay'))

        for name, cmd in zip(control_name, control_code):
            # loop over the control values
            if not config.has_option('control', name):
                continue # it should be skipped when commented out in the ini file
            val = r.get(config.get('control', name))
            if val:
                val = float(val)
            else:
                continue # it should be skipped when not present
            val = int(val)
            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            previous_val[name] = val
            msg = mido.Message('control_change', control=cmd, value=val, channel=midichannel)
            if debug>1:
                print cmd, val, name
            lock.acquire()
            outputport.send(msg)
            lock.release()

except KeyboardInterrupt:
    print "Closing threads"
    for thread in trigger:
        thread.stop()
    r.publish('VOLCABEATS_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
