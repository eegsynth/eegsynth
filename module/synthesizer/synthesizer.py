#!/usr/bin/env python

import math
import pyaudio
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis

config = ConfigParser.ConfigParser()
config.read('synthesizer.ini')

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
p = pyaudio.PyAudio()

BITRATE   = int(config.get('general', 'bitrate'))
BLOCKSIZE = int(config.get('general', 'blocksize'))
FREQUENCY = 256.0
BITS = p.get_format_from_width(1)
CHANNELS = 1

stream = p.open(format = BITS, channels = CHANNELS, rate = BITRATE, output = True)

offset = 0
while True:

  ampl_sin = r.get(config.get('input', 'ampl_sin'))
  if ampl_sin:
    ampl_sin = float(ampl_sin)
  else:
    ampl_sin = config.getfloat('default','ampl_sin')

  ampl_sqr = r.get(config.get('input', 'ampl_sqr'))
  if ampl_sqr:
    ampl_sqr = float(ampl_sqr)
  else:
    ampl_sqr = config.getfloat('default','ampl_sqr')

  ampl_tri = r.get(config.get('input', 'ampl_tri'))
  if ampl_tri:
    ampl_tri = float(ampl_tri)
  else:
    ampl_tri = config.getfloat('default','ampl_tri')

  ampl_saw = r.get(config.get('input', 'ampl_saw'))
  if ampl_saw:
    ampl_saw = float(ampl_saw)
  else:
    ampl_saw = config.getfloat('default','ampl_saw')

  ampl_total = ampl_sin + ampl_sqr + ampl_tri + ampl_saw
  if ampl_total>0:
      ampl_sin = ampl_sin/ampl_total
      ampl_sqr = ampl_sqr/ampl_total
      ampl_tri = ampl_tri/ampl_total
      ampl_saw = ampl_saw/ampl_total

  BUFFER = ''
  PERIOD = int(BITRATE/FREQUENCY)
  for t in xrange(offset, offset+BLOCKSIZE):
    wave_sin = ampl_sin * (math.sin(math.pi*FREQUENCY*t/BITRATE)+1)/2
    wave_sqr = ampl_sqr * float((t % PERIOD) > PERIOD/2)
    wave_tri = ampl_tri * float(abs(t % PERIOD - PERIOD/2))/PERIOD*2
    wave_saw = ampl_saw * float(t % PERIOD)/PERIOD
    waveform = (wave_sin + wave_sqr + wave_tri + wave_saw)*255
    BUFFER = BUFFER+chr(int(waveform))
  offset = offset+BLOCKSIZE
  stream.write(BUFFER)

stream.stop_stream()
stream.close()
p.terminate()
