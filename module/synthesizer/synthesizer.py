#!/usr/bin/env python

# Synthesizer acts as a basic synthesizer
#
# Synthesizer is part of the EEGsynth project (https://github.com/eegsynth/eegsynth)
#
# Copyright (C) 2017 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import argparse
import math
import multiprocessing
import os
import pyaudio
import redis
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    basis = sys.executable
else:
    basis = sys.argv[0]
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

def default(x, y):
    if x is None:
        return y
    else:
        return x

p = pyaudio.PyAudio()

devices = []
for i in range(p.get_device_count()):
    devices.append(p.get_device_info_by_index(i))
print('-------------------------')
for i, dev in enumerate(devices):
    print "%d - %s" % (i, dev['name'])
print('-------------------------')

BLOCKSIZE = int(config.get('general','blocksize'))
CHANNELS  = 1
BITRATE   = int(config.get('general','bitrate'))
BITS      = p.get_format_from_width(1)

lock = threading.Lock()

stream = p.open(format = BITS,
		channels = CHANNELS,
		rate = BITRATE,
		output = True,
		output_device_index = config.getint('pyaudio','output_device_index'))

class TriggerThread(threading.Thread):
    def __init__(self, r, config):
        threading.Thread.__init__(self)
        self.r = r
        self.config = config
        self.running = True
        lock.acquire()
        self.time = 0
        self.last = 0
        lock.release()
    def stop(self):
        self.running = False
    def run(self):
        pubsub = self.r.pubsub()
        channel = self.config.get('input','adsr_gate')
        pubsub.subscribe(channel)
        while self.running:
           for item in pubsub.listen():
               if not self.running or not item['type'] == 'message':
                   break
               print item['channel'], "=", item['data']
               lock.acquire()
               self.last = self.time
               lock.release()

class ControlThread(threading.Thread):
    def __init__(self, r, config):
        threading.Thread.__init__(self)
        self.r = r
        self.config = config
        self.running = True
        lock.acquire()
        self.vco_pitch      = 0
        self.vco_sin        = 0
        self.vco_tri        = 0
        self.vco_saw        = 0
        self.vco_sqr        = 0
        self.lfo_depth      = 0
        self.lfo_frequency  = 0
        self.adsr_attack    = 0
        self.adsr_decay     = 0
        self.adsr_sustain   = 0
        self.adsr_release   = 0
        self.vca_envelope   = 0
        lock.release()
    def stop(self):
        self.running = False
    def run(self):
      while self.running:

          ################################################################################
          # VCO
          ################################################################################
          vco_pitch = self.r.get(config.get('input','vco_pitch'))
          if vco_pitch:
              vco_pitch = float(vco_pitch)
          else:
              vco_pitch = self.config.getfloat('default','vco_pitch')

          vco_sin = self.r.get(self.config.get('input','vco_sin'))
          if vco_sin:
              vco_sin = float(vco_sin)
          else:
              vco_sin = self.config.getfloat('default','vco_sin')

          vco_tri = self.r.get(self.config.get('input','vco_tri'))
          if vco_tri:
              vco_tri = float(vco_tri)
          else:
              vco_tri = self.config.getfloat('default','vco_tri')

          vco_saw = self.r.get(self.config.get('input','vco_saw'))
          if vco_saw:
              vco_saw = float(vco_saw)
          else:
              vco_saw = self.config.getfloat('default','vco_saw')

          vco_sqr = self.r.get(self.config.get('input','vco_sqr'))
          if vco_sqr:
              vco_sqr = float(vco_sqr)
          else:
            vco_sqr = self.config.getfloat('default','vco_sqr')

          vco_total = vco_sin + vco_tri + vco_saw + vco_sqr
          if vco_total>0:
              # these are all scaled relatively to each other
              vco_sin = vco_sin/vco_total
              vco_tri = vco_tri/vco_total
              vco_saw = vco_saw/vco_total
              vco_sqr = vco_sqr/vco_total

          ################################################################################
          # LFO
          ################################################################################
          lfo_frequency = self.r.get(self.config.get('input','lfo_frequency'))
          if lfo_frequency:
              lfo_frequency = float(lfo_frequency)
          else:
              lfo_frequency = self.config.getfloat('default','lfo_frequency')
          # assume that this value is between 0 and 127
          lfo_frequency = lfo_frequency/3

          lfo_depth = self.r.get(self.config.get('input','lfo_depth'))
          if lfo_depth:
              lfo_depth = float(lfo_depth)
          else:
              lfo_depth = self.config.getfloat('default','lfo_depth')
          # assume that this value is between 0 and 127
          lfo_depth = lfo_depth/127

          ################################################################################
          # ADSR
          ################################################################################
          adsr_attack = self.r.get(self.config.get('input','adsr_attack'))
          if adsr_attack:
              adsr_attack = float(adsr_attack)
          else:
              adsr_attack = self.config.getfloat('default','adsr_attack')

          adsr_decay = self.r.get(self.config.get('input','adsr_decay'))
          if adsr_decay:
              adsr_decay = float(adsr_decay)
          else:
              adsr_decay = self.config.getfloat('default','adsr_decay')

          adsr_sustain = self.r.get(self.config.get('input','adsr_sustain'))
          if adsr_sustain:
              adsr_sustain = float(adsr_sustain)
          else:
              adsr_sustain = self.config.getfloat('default','adsr_sustain')

          adsr_release = self.r.get(self.config.get('input','adsr_release'))
          if adsr_release:
              adsr_release = float(adsr_release)
          else:
              adsr_release = self.config.getfloat('default','adsr_release')

          # convert from value between 0 and 127 into time in samples
          adsr_attack   *= float(BITRATE)/127
          adsr_decay    *= float(BITRATE)/127
          adsr_sustain  *= float(BITRATE)/127
          adsr_release  *= float(BITRATE)/127

          ################################################################################
          # VCA
          ################################################################################
          vca_envelope = self.r.get(self.config.get('input','vca_envelope'))
          if vca_envelope:
              vca_envelope = float(vca_envelope)
          else:
              vca_envelope = self.config.getfloat('default','vca_envelope')
          # assume that this value is between 0 and 127
          vca_envelope = vca_envelope/127.0

          ################################################################################
          # store the control values in the local object
          ################################################################################
          lock.acquire()
          self.vco_pitch        = vco_pitch
          self.vco_sin          = vco_sin
          self.vco_tri          = vco_tri
          self.vco_saw          = vco_saw
          self.vco_sqr          = vco_sqr
          self.lfo_depth        = lfo_depth
          self.lfo_frequency    = lfo_frequency
          self.adsr_attack      = adsr_attack
          self.adsr_decay       = adsr_decay
          self.adsr_sustain     = adsr_sustain
          self.adsr_release     = adsr_release
          self.vca_envelope     = vca_envelope
          lock.release()

# start the background thread that deals with control value changes
control = ControlThread(r, config)
control.start()

# start the background thread that deals with triggers
trigger = TriggerThread(r, config)
trigger.start()

offset = 0
try:
  while True:
    ################################################################################
    # generate the signal
    ################################################################################
    BUFFER = ''

    for t in xrange(offset,offset+BLOCKSIZE):
        # update the time for the trigger detection

        lock.acquire()
        trigger.time    = t
        last            = trigger.last
        vco_pitch       = control.vco_pitch
        vco_sin         = control.vco_sin
        vco_tri         = control.vco_tri
        vco_saw         = control.vco_saw
        vco_sqr         = control.vco_sqr
        lfo_depth       = control.lfo_depth
        lfo_frequency   = control.lfo_frequency
        adsr_attack     = control.adsr_attack
        adsr_decay      = control.adsr_decay
        adsr_sustain    = control.adsr_sustain
        adsr_release    = control.adsr_release
        vca_envelope    = control.vca_envelope
        lock.release()

        # compose the VCO waveform
        if vco_pitch>0:
            # note 60 on the keyboard is the C4, which is 261.63 Hz
            # note 72 on the keyboard is the C5, which is 523.25 Hz
            FREQUENCY = math.pow(2, (vco_pitch/12-4))*261.63
            PERIOD = int(BITRATE/FREQUENCY)
            wave_sin = vco_sin * (math.sin(math.pi*FREQUENCY*t/BITRATE)+1)/2
            wave_tri = vco_tri * float(abs(t % PERIOD - PERIOD/2))/PERIOD*2
            wave_saw = vco_saw * float(t % PERIOD)/PERIOD
            wave_sqr = vco_sqr * float((t % PERIOD) > PERIOD/2)
            waveform = (wave_sin + wave_tri + wave_saw + wave_sqr)*127
        else:
            waveform = 0

        # compose and apply the LFO
        lfo_envelope = (math.sin(math.pi*lfo_frequency*t/BITRATE)+1)/2
        lfo_envelope = lfo_depth + (1-lfo_depth)*lfo_envelope
        waveform = lfo_envelope * waveform

        # compose and apply the ADSR
        if adsr_attack>0 and (t-last)<adsr_attack:
            adsr_envelope = (t-last)/adsr_attack
        elif adsr_decay>0 and (t-last-adsr_attack)<adsr_decay:
            adsr_envelope = 1.0 - 0.5*(t-last-adsr_attack)/adsr_decay
        elif adsr_sustain>0 and (t-last-adsr_attack-adsr_decay)<adsr_sustain:
            adsr_envelope = 0.5
        elif adsr_release>0 and (t-last-adsr_attack-adsr_decay-adsr_sustain)<adsr_release:
            adsr_envelope = 0.5 - 0.5*(t-last-adsr_attack-adsr_decay-adsr_sustain)/adsr_release
        else:
            adsr_envelope = 0
        waveform = adsr_envelope * waveform

        # apply the VCA
        waveform = vca_envelope * waveform

        # add the current waveform sample to the buffer
        BUFFER = BUFFER+chr(int(waveform))

    # write the buffer content to the audio device
    stream.write(BUFFER)
    offset = offset+BLOCKSIZE

except KeyboardInterrupt:
    trigger.stop()
    control.stop()
    trigger.join()
    control.join()
    stream.stop_stream()
    stream.close()
    p.terminate()
