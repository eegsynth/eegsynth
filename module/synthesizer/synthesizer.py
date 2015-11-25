#!/usr/bin/env python

import math
import pyaudio
import ConfigParser # this is version 2.x specific,on version 3.x it is called "configparser" and has a different API
import redis

config = ConfigParser.ConfigParser()
config.read('synthesizer.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'),port=config.getint('redis','port'),db=0)
p = pyaudio.PyAudio()

BITRATE   = int(config.get('general','bitrate'))
BLOCKSIZE = int(config.get('general','blocksize'))
CHANNELS  = 1
BITS = p.get_format_from_width(1)

stream = p.open(format = BITS,channels = CHANNELS,rate = BITRATE,output = True)

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
    FREQUENCY = math.pow(2, (pitch/12-5))*261.63

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
  # generate the signal
  ################################################################################

  BUFFER = ''
  PERIOD = int(BITRATE/FREQUENCY)
  for t in xrange(offset,offset+BLOCKSIZE):
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
    # apply the VCA
    waveform = control_vca * waveform
    BUFFER = BUFFER+chr(int(waveform))
  offset = offset+BLOCKSIZE
  stream.write(BUFFER)

stream.stop_stream()
stream.close()
p.terminate()
