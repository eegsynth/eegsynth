#!/usr/bin/env python

import mido
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import threading
import time
import sys
import os
import argparse

# the list of MIDI commands is the only aspect that is specific to the Volca Keys
# see http://media.aadl.org/files/catalog_guides/1444140_chart.pdf
control_name = ['portamento', 'expression', 'voice', 'octave', 'detune', 'vco_eg_int', 'vcf_cutoff', 'vcf_eg_int', 'lfo_rate', 'lfo_pitch_int', 'lfo_cutoff_int', 'eg_attack', 'eg_decay_release', 'eg_sustain', 'delay_time', 'delay_feedback']
control_code = [5, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]
note_name = ['C0', 'Db0', 'D0', 'Eb0', 'E0', 'F0', 'Gb0', 'G0', 'Ab0', 'A0', 'Bb0', 'B0', 'C1', 'Db1', 'D1', 'Eb1', 'E1', 'F1', 'Gb1', 'G1', 'Ab1', 'A1', 'Bb1', 'B1', 'C2', 'Db2', 'D2', 'Eb2', 'E2', 'F2', 'Gb2', 'G2', 'Ab2', 'A2', 'Bb2', 'B2', 'C3', 'Db3', 'D3', 'Eb3', 'E3', 'F3', 'Gb3', 'G3', 'Ab3', 'A3', 'Bb3', 'B3', 'C4', 'Db4', 'D4', 'Eb4', 'E4', 'F4', 'Gb4', 'G4', 'Ab4', 'A4', 'Bb4', 'B4', 'C5', 'Db5', 'D5', 'Eb5', 'E5', 'F5', 'Gb5', 'G5', 'Ab5', 'A5', 'Bb5', 'B5', 'C6', 'Db6', 'D6', 'Eb6', 'E6', 'F6', 'Gb6', 'G6', 'Ab6', 'A6', 'Bb6', 'B6', 'C7', 'Db7', 'D7', 'Eb7', 'E7', 'F7', 'Gb7', 'G7', 'Ab7', 'A7', 'Bb7', 'B7', 'C8', 'Db8', 'D8', 'Eb8', 'E8', 'F8', 'Gb8', 'G8', 'Ab8', 'A8', 'Bb8', 'B8', 'C9', 'Db9', 'D9', 'Eb9', 'E9', 'F9', 'Gb9', 'G9', 'Ab9', 'A9', 'Bb9', 'B9', 'C10', 'Db10', 'D10', 'Eb10', 'E10', 'F10', 'Gb10', 'G10', 'Ab10', 'A10', 'Bb10', 'B10']
note_code = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143]

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
        pubsub.subscribe('VOLCAKEYS_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)    # this message contains the note
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
    if config.has_option('note', name):
        # start the background thread that deals with this note
        this = TriggerThread(config.get('note', name), code)
        trigger.append(this)
        if debug>1:
            print name, 'OK'

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
    r.publish('VOLCAKEYS_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
