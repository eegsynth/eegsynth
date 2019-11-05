#!/usr/bin/env python3

# This software is part of the EEGsynth project,
# see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017-2019 EEGsynth project
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

import pyqtgraph as pg
import numpy as np
import configparser
import argparse
import os
import redis
import sys
import time
from scipy.signal import decimate, detrend
from spectrum import arburg, arma2psd
from pyqtgraph.Qt import QtGui


if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
elif sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
else:
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path,'../../lib'))
import FieldTrip
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument('-i',
                    '--inifile',
                    default=os.path.join(path,
                                         os.path.splitext(file)[0] + '.ini'),
                    help='optional name of the configuration file')
args = parser.parse_args()
config = configparser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'),
                          port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError('cannot connect to Redis server')

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)
del config

# get the options from the configuration file
debug = patch.getint('general', 'debug')
timeout = patch.getfloat('fieldtrip', 'timeout')
channel = patch.getint('input', 'channel') - 1
key_rate = patch.getstring('output', 'key')
stride = patch.getfloat('general', 'delay')
downsampsfreq = patch.getint("processing", "downsamplingsfreq")
t = patch.getint("processing", "window")

try:
    ftc_host = patch.getstring('fieldtrip', 'hostname')
    ftc_port = patch.getint('fieldtrip', 'port')
    if debug > 0:
        print('Trying to connect to buffer on {}:{} ...'.format(ftc_host,
              ftc_port))
    ft_input = FieldTrip.Client()
    ft_input.connect(ftc_host, ftc_port)
    if debug > 0:
        print('connected to input FieldTrip buffer')
except:
    raise RuntimeError('cannot connect to input FieldTrip buffer')

hdr_input = None
start = time.time()
while hdr_input is None:
    if debug > 0:
        print('waiting for data to arrive...')
    if (time.time() - start) > timeout:
        print('error: timeout while waiting for data')
        raise SystemExit
    hdr_input = ft_input.getHeader()
    time.sleep(0.1)

if debug>0:
    print('data arrived')
if debug>1:
    print(hdr_input)
    print(hdr_input.labels)

sfreq = hdr_input.fSample
window = int(np.rint(t * sfreq))
downsampfact = sfreq / downsampsfreq
freqs = np.fft.rfftfreq(window, 1 / sfreq)

begsample = -1
endsample = -1

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth plotspectral")
spectrum = win.addPlot(title="AR Spectrum")
spectrum.setLabel('left', text='Power')
spectrum.setLabel('bottom', text='Frequency (Hz)')
# start plotting
QtGui.QApplication.instance().exec_()

while True:

    # window shift implicitely controlled with temporal delay; to
    # be able to change this "on the fly" read out stride from the patch
    # inside the loop if desired
    time.sleep(stride)

    hdr_input = ft_input.getHeader()
    if (hdr_input.nSamples - 1) < endsample:
        print('error: buffer reset detected')
        raise SystemExit
    if hdr_input.nSamples < window:
        # there are not yet enough samples in the buffer
        if debug > 0:
            print('waiting for data...')
        continue

    # grab the next window
    begsample = hdr_input.nSamples - window
    endsample = hdr_input.nSamples - 1
    dat = ft_input.getData([begsample, endsample])
    dat = dat[:, channel]

    # downsample signal, using scipy.signal.decimate (important to use fir not iir)
    dat = decimate(dat, downsampfact, ftype="fir")

    # detrend and taper the signal
    dat = detrend(dat)
    dat *= np.hanning(window)

    # compute AR coefficients
    AR, rho, _ = arburg(dat, order=16)
    # use coefficients to compute spectral estimate
    pburg = arma2psd(AR, rho=rho, NFFT=window)
    # select only positive frequencies
    pburg = np.flip(pburg[t:])

    # update the spectrum
    spectrum.setData(freqs, pburg)

    pg.QtGui.QApplication.processEvents()
