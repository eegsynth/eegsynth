#!/usr/bin/env python

import sys
import os
import time
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import numpy as np

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
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    ftc_host = config.get('input_fieldtrip','hostname')
    ftc_port = config.getint('input_fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to input FieldTrip buffer"
except:
    print "Error: cannot connect to input FieldTrip buffer"
    exit()

try:
    ftc_host = config.get('output_fieldtrip','hostname')
    ftc_port = config.getint('output_fieldtrip','port')
    if debug>0:
        print 'Trying to connect to buffer on %s:%i ...' % (ftc_host, ftc_port)
    ft_output = FieldTrip.Client()
    ft_output.connect(ftc_host, ftc_port)
    if debug>0:
        print "Connected to output FieldTrip buffer"
except:
    print "Error: cannot connect to output FieldTrip buffer"
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

# get the input and output options
input_number, input_channel = map(list, zip(*config.items('input_channel')))
output_number, output_channel = map(list, zip(*config.items('output_channel')))
montage_number, montage_equation = map(list, zip(*config.items('montage')))
# convert to integer and make the indices zero-offset
input_number = [int(number)-1 for number in input_number]
output_number = [int(number)-1 for number in output_number]
montage_number = [int(number)-1 for number in montage_number]

def sanitize(equation):
    equation = equation.replace('(', '( ')
    equation = equation.replace(')', ' )')
    equation = equation.replace('+', ' + ')
    equation = equation.replace('-', ' - ')
    equation = equation.replace('*', ' * ')
    equation = equation.replace('/', ' / ')
    equation = equation.replace('  ', ' ')
    return equation

# make the equations robust against sub-string replacements
montage_equation = [sanitize(equation) for equation in montage_equation]

# ensure that all input channels have a label
nInputs = hdr_input.nChannels
if len(hdr_input.labels)==0:
    for i in range(nInputs):
        hdr_input.labels.append('{}'.format(i+1))
# update the labels with the ones specified in the ini file
for number,channel in zip(input_number, input_channel):
    if number<nInputs:
        hdr_input.labels[number] = channel
# update the input channel specification
input_number = range(nInputs)
input_channel = hdr_input.labels

# ensure that all output channels have a label
nOutputs = max(output_number+montage_number)+1
tmp = ['{}'.format(i+1) for i in range(nOutputs)]
for number,channel in zip(output_number, output_channel):
    tmp[number] = channel
# update the output channel specification
output_number = range(nOutputs)
output_channel = tmp

if debug>0:
    print '===== input channels ====='
    for number,channel in zip(input_number, input_channel):
        print number, '=', channel
    print '===== output channels ====='
    for number,channel in zip(output_number, output_channel):
        print number, '=', channel

identity = np.identity(nInputs, dtype=np.float32)
montage  = np.zeros((nInputs,nOutputs), dtype=np.float32)
previous = np.zeros((1,nOutputs)) # for exponential smoothing

# construct a weighting matrix to map input to output data
# replace the channel names in the output equation with the corresponding column of the identity matrix
for index,equation in zip(montage_number,montage_equation):
    for number,channel in zip(input_number, input_channel):
        equation = equation.replace(channel, 'identity[:,{}]'.format(number))
    montage[:,index] = eval(equation)

if debug>0:
    print '======== montage ========='
    for number,equation in zip(montage_number, montage_equation):
        print number, '=', equation

if debug>1:
    print '======== montage ========='
    print montage

smoothing = config.getfloat('processing','smoothing')
window = config.getfloat('processing','window')
window = int(round(window*hdr_input.fSample))

begsample = -1
while begsample<0:
    # wait until there is enough data
    hdr_input = ft_input.getHeader()
    # jump to the end of the stream
    begsample = int(hdr_input.nSamples - window)
    endsample = int(hdr_input.nSamples - 1)

ft_output.putHeader(nOutputs, hdr_input.fSample, hdr_input.dataType, labels=output_channel)

while True:

    while endsample>hdr_input.nSamples-1:
        # wait until there is enough data
        time.sleep(config.getfloat('general', 'delay'))
        hdr_input = ft_input.getHeader()

    if debug>1:
        print endsample

    dat_input = ft_input.getData([begsample, endsample])
    dat_output = dat_input.dot(montage).astype(np.float32)

    for t in range(window):
        dat_output[t,:] = smoothing * dat_output[t,:] + (1.-smoothing)*previous
        previous = dat_output[t,:]

    # write the data to the output buffer
    ft_output.putData(dat_output)
    # increment the counters for the next loop
    begsample += window
    endsample += window
