#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np
import matplotlib.pyplot as plt

basis = '/Users/csmfindling/Documents/eeggames/eegsynth/module/plot/'

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

config = ConfigParser.ConfigParser()

try:
    config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))
except:
    __file__ = 'plot.py'
    config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    ftc_host = config.get('fieldtrip','hostname')
    ftc_port = config.getint('fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

hdr_input = None
while hdr_input is None:
    if debug>0:
        print "Waiting for data to arrive..."
    hdr_input = ft_input.getHeader()
    time.sleep(0.2)

if debug>1:
    print hdr_input
    print hdr_input.labels

# ensure that all input channels have a label
nInputs = hdr_input.nChannels
if len(hdr_input.labels)==0:
    for i in range(nInputs):
        hdr_input.labels.append('{}'.format(i+1))

# get the input and output options
try:
    input_number, input_channel = map(list, zip(*config.items('channels')))

    # convert to integer and make the indices zero-offset
    input_number = [int(number)-1 for number in input_number]

    # update the labels with the ones specified in the ini file
    for number,channel in zip(input_number, input_channel):
        if number<nInputs:
            hdr_input.labels[number] = channel
except:
    pass

# get plot channels
plot_channels = np.where(np.asarray([config.items('plot_channels')[i][1]=='on' for i in range(len(config.items('plot_channels')))]))[0]

window    = config.getfloat('arguments','window')
window    = int(round(window*hdr_input.fSample))


if config.get('arguments','ylim').split(',')[1].replace(' ', '')[:-1] != 'inf' and config.get('arguments','ylim').split(',')[0].replace(' ', '')[2:] != 'inf':
    ymin = float(config.get('arguments','ylim').split(',')[0].replace(' ', '')[1:])
    ymax = float(config.get('arguments','ylim').split(',')[1].replace(' ', '')[:-1])
else:
    ymax=np.inf

begsample = -1
while begsample<0:
    # wait until there is enough data
    hdr_input = ft_input.getHeader()
    # jump to the end of the stream
    begsample = int(hdr_input.nSamples - window)
    endsample = int(hdr_input.nSamples - 1)

plt.figure(figsize=np.asarray(config.get('arguments','figsize')[1:-1].split(','), dtype=np.int)); plt.ion();

while True:

    if debug>1:
        print endsample

    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(config.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()

    data = ft_input.getData([begsample, endsample])[:, plot_channels]

    plt.plot(data, linewidth=config.getfloat('arguments','linewidth'))
    plt.draw()
    plt.show()
    plt.xlabel(config.get('arguments','xlabel')); plt.ylabel(config.get('arguments','ylabel'))
    if ymax!=np.inf:
        plt.axis([0, len(data), ymin, ymax])
    plt.title(config.get('arguments', 'title'), fontsize=config.getfloat('arguments', 'fontsize'))
    plt.pause(config.getfloat('general', 'delay'))
    plt.hold(False)

    # increment the counters for the next loop
    begsample += window
    endsample += window



