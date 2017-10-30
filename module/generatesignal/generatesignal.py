#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np
import argparse

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
import FieldTrip

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
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

try:
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
    exit()

nchannels = config.getint('generate', 'nchannels')
fsample   = config.getfloat('generate', 'fsample')
window    = int(round(config.getfloat('generate', 'window') * fsample))
datatype  = FieldTrip.DATATYPE_FLOAT32

ft_output.putHeader(nchannels, fsample, datatype)

if debug > 1:
    print "nchannels", nchannels
    print "fsample", fsample
    print "window", window

begsample = 0
endsample = window

scale_frequency   = config.getfloat('scale', 'frequency')
scale_amplitude   = config.getfloat('scale', 'amplitude')
scale_noise       = config.getfloat('scale', 'noise')

prev_frequency = -1
prev_amplitude = -1
prev_noise     = -1

print "STARTING STREAM"
while True:

    start = time.time();
    
    frequency = EEGsynth.getfloat('signal', 'frequency', config, r, default=10) * scale_frequency
    amplitude = EEGsynth.getfloat('signal', 'amplitude', config, r, default=1)  * scale_amplitude
    noise     = EEGsynth.getfloat('signal', 'noise', config, r, default=0.5)    * scale_noise

    if frequency != prev_frequency:
        print "frequency", frequency
        prev_frequency = frequency
    if amplitude != prev_amplitude:
        print "amplitude =", amplitude
        prev_amplitude = amplitude
    if noise != prev_noise:
        print "noise =", noise
        prev_noise = noise

    dat_output = np.random.randn(window, nchannels) * noise
    signal = np.sin(2*np.pi*np.arange(begsample, endsample)*frequency/fsample) * amplitude
    for chan in range(nchannels):
        dat_output[:,chan] += signal

    # write the data to the output buffer
    ft_output.putData(dat_output.astype(np.float32))

    if debug>0:
        print "generated", window, "samples in", (time.time()-start)*1000, "ms"

    begsample += window
    endsample += window

    # wait for a little bit
    elapsed = time.time()-start
    time.sleep(window/fsample - elapsed); 

