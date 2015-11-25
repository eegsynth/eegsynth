#!/usr/bin/env python

import math
import pyaudio
import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import redis
import multiprocessing
import time as _time

config = ConfigParser.ConfigParser()
config.read('synthesizer.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'),port=config.getint('redis','port'),db=0)
p = pyaudio.PyAudio()

BITRATE   = int(config.get('general','bitrate'))
BLOCKSIZE = int(config.get('general','blocksize'))
CHANNELS  = 1
BITS = p.get_format_from_width(1)

stream = p.open(format = BITS,channels = CHANNELS,rate = BITRATE,output = True)

time = multiprocessing.Value('d', 0)
last = multiprocessing.Value('d', 0)

def TriggerMonitor(r, channel):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    for item in pubsub.listen():
        print item['channel'], ":", item['data']
        last.value = time.value

trigger = multiprocessing.Process(target=TriggerMonitor, args=(r, config.get('input','adsr_gate')))
trigger.start()

offset = 0
while True:

  ################################################################################
  # VCO
  ################################################################################

  pitch = r.get(config.get('input','pitch'))
  if pitch:
    pitch = float(pitch)
  else:
    pitch = config.getfloat('default','pitch')

  if config.get('general','taper')=='linear':
    # see http://www.resistorguide.com/potentiometer-taper/
    # assume that this value is between 0 and 127
    # map it to a comfortable frequency range
    FREQUENCY = 10*pitch + 1
  else:
    # note 60 on the keyboard is the C4, which is 261.63 Hz
    # note 72 on the keyboard is the C5, which is 523.25 Hz
    FREQUENCY = math.pow(2, (pitch/12-4))*261.63

  control_sin = r.get(config.get('input','sin'))
  if control_sin:
    control_sin = float(control_sin)
  else:
    control_sin = config.getfloat('default','sin')

  control_tri = r.get(config.get('input','tri'))
  if control_tri:
    control_tri = float(control_tri)
  else:
    control_tri = config.getfloat('default','tri')

  control_saw = r.get(config.get('input','saw'))
  if control_saw:
    control_saw = float(control_saw)
  else:
    control_saw = config.getfloat('default','saw')

  control_sqr = r.get(config.get('input','sqr'))
  if control_sqr:
    control_sqr = float(control_sqr)
  else:
    control_sqr = config.getfloat('default','sqr')

  control_total = control_sin + control_tri + control_saw + control_sqr
  if control_total>0:
      # these are all scaled relatively to each other
      control_sin = control_sin/control_total
      control_tri = control_tri/control_total
      control_saw = control_saw/control_total
      control_sqr = control_sqr/control_total

  ################################################################################
  # LFO
  ################################################################################

  lfo_frequency = r.get(config.get('input','lfo_frequency'))
  if lfo_frequency:
    lfo_frequency = float(lfo_frequency)
  else:
    lfo_frequency = config.getfloat('default','lfo_frequency')
  # assume that this value is between 0 and 127
  lfo_frequency = lfo_frequency/3

  lfo_depth = r.get(config.get('input','lfo_depth'))
  if lfo_depth:
    lfo_depth = float(lfo_depth)
  else:
    lfo_depth = config.getfloat('default','lfo_depth')
  # assume that this value is between 0 and 127
  lfo_depth = lfo_depth/127

  ################################################################################
  # VCA
  ################################################################################

  control_vca = r.get(config.get('input','vca'))
  if control_vca:
    control_vca = float(control_vca)
  else:
    control_vca = config.getfloat('default','vca')
  # assume that this value is between 0 and 127
  control_vca = control_vca/127.0

  ################################################################################
  # ADSR
  ################################################################################

  control_attack = r.get(config.get('input','adsr_attack'))
  if control_attack:
    control_attack = float(control_attack)
  else:
    control_attack = config.getfloat('default','adsr_attack')

  control_decay = r.get(config.get('input','adsr_decay'))
  if control_decay:
    control_decay = float(control_decay)
  else:
    control_decay = config.getfloat('default','adsr_decay')

  control_sustain = r.get(config.get('input','adsr_sustain'))
  if control_sustain:
    control_sustain = float(control_sustain)
  else:
    control_sustain = config.getfloat('default','adsr_sustain')

  control_release = r.get(config.get('input','adsr_release'))
  if control_release:
    control_release = float(control_release)
  else:
    control_release = config.getfloat('default','adsr_release')

  # convert from value between 0 and 127 into time in samples
  control_attack  *= float(BITRATE)/127
  control_decay   *= float(BITRATE)/127
  control_sustain *= float(BITRATE)/127
  control_release *= float(BITRATE)/127

  ################################################################################
  # generate the signal
  ################################################################################

  BUFFER = ''
  PERIOD = int(BITRATE/FREQUENCY)
  for t in xrange(offset,offset+BLOCKSIZE):
    # update the time for the trigger detection
    time.value = t

    # compose the VCO
    wave_sin = control_sin * (math.sin(math.pi*FREQUENCY*t/BITRATE)+1)/2
    wave_tri = control_tri * float(abs(t % PERIOD - PERIOD/2))/PERIOD*2
    wave_saw = control_saw * float(t % PERIOD)/PERIOD
    wave_sqr = control_sqr * float((t % PERIOD) > PERIOD/2)
    waveform = (wave_sin + wave_tri + wave_saw + wave_sqr)*127
    # compose and apply the LFO
    control_lfo = (math.sin(math.pi*lfo_frequency*t/BITRATE)+1)/2
    control_lfo = lfo_depth + (1-lfo_depth)*control_lfo
    waveform = control_lfo * waveform

    # compose and apply the ADSR
    if control_attack>0 and (t-last.value)<control_attack:
        control_adsr = (t-last.value)/control_attack
    elif control_decay>0 and (t-last.value-control_attack)<control_decay:
        control_adsr = 1.0 - 0.5*(t-last.value-control_attack)/control_decay
    elif control_sustain>0 and (t-last.value-control_attack-control_decay)<control_sustain:
        control_adsr = 0.5
    elif control_release>0 and (t-last.value-control_attack-control_decay-control_sustain)<control_release:
        control_adsr = 0.5 - 0.5*(t-last.value-control_attack-control_decay-control_sustain)/control_release
    else:
        control_adsr = 0
    waveform = control_adsr * waveform

    # apply the VCA
    waveform = control_vca * waveform
    BUFFER = BUFFER+chr(int(waveform))
  offset = offset+BLOCKSIZE
  stream.write(BUFFER)
 
stream.stop_stream()
stream.close()
p.terminate()
