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
import signal
from scipy.signal import decimate, detrend
from scipy.interpolate import interp1d
#from spectrum import arburg, arma2psd
from pyqtgraph.Qt import QtGui, QtCore
from numpy.fft import rfft, rfftfreq


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
sfreq_downsamp = patch.getint("processing", "downsamplesfreq")
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
downsampfact = int(sfreq / sfreq_downsamp)
window = int(np.rint(t * sfreq))
window_downsamp = int(np.rint(t * sfreq_downsamp))
freqs = rfftfreq(window_downsamp, 1 / sfreq_downsamp)
freqres = 1 / t
interpres = 0.025
freqsintp = np.arange(freqs[0], freqs[-1], interpres)

# limits are hardcoded for now, get them from ini file eventually
# limits must be multiples of interpres
target = 0.1
lowreward = 0.06
upreward = 0.14
lowtotal = 0
uptotal = 0.5
rewardrange = np.logical_and(freqsintp >= lowreward, freqsintp <= upreward)
totalrange = np.logical_and(freqsintp >= lowtotal, freqsintp <= uptotal)

# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="Breathing Frequency")
psdplot = win.addPlot(title="PSD", row=0, col=0, rowspan=4, colspan=6)
fdbkvalue = win.addLabel(row=0, col=6)
psdcurve = psdplot.plot()
psdcurve.setData(freqsintp, np.zeros(np.size(freqsintp)))
psdplot.setLabel('left', text='Power (a.u.)')
psdplot.setLabel('bottom', text='Frequency (Hz)')

brush = QtGui.QBrush(QtGui.QColor(0, 255, 0, 50))
rewardregion = pg.LinearRegionItem(bounds=[lowreward, upreward], movable=False,
                                   brush=brush)
psdplot.addItem(rewardregion)

pg.setConfigOptions(antialias=True)


def update():
    
    # grab the next window from the buffer
    last_idx = ft_input.getHeader().nSamples
    begsample = last_idx - window
    endsample = last_idx - 1
    dat = ft_input.getData([begsample, endsample]).astype(np.double)
    dat = dat[:, channel]

    # downsample signal, using scipy.signal.decimate (important to use fir not iir)
    dat = decimate(dat, downsampfact, ftype="fir")

    # detrend and taper the signal
    dat = detrend(dat)
    dat *= np.hanning(window_downsamp)

#    # compute AR coefficients
#    AR, rho, _ = arburg(dat, order=16)
#    # use coefficients to compute spectral estimate
#    psd = arma2psd(AR, rho=rho, NFFT=window)
#    # select only positive frequencies
#    psd = np.flip(psd[t:])

    psd = abs(rfft(dat))
    
    # interpolate psd at desired frequency resolution in order to be able to 
    # set feedback thresholds at intervals smaller than the original frequency
    # resolution
    f = interp1d(freqs, psd)
    psdintp = f(freqsintp)
    # update the spectrum
    psdcurve.setData(freqsintp, psdintp)
    rewardpsd = np.sum(psdintp[rewardrange])
    totalpsd = np.sum(psdintp[totalrange])
    # increase rewardrange and/or decrease totalrange to make it easier to
    # achieve positive feedback, i.e., rewardratio >= 1
    rewardratio = rewardpsd / (totalpsd - rewardpsd)
    # 1 corresponds to best visibility, 0 to the poorest, Feedback value
    # must be send as float
    if rewardratio > 1:
        rewardratio = 1
    patch.setvalue("Feedback", float(rewardratio))
    fdbkvalue.setText(str(np.around(rewardratio, decimals=2)), size='50pt')
    print(float(rewardratio))
    

# keyboard interrupt handling
def sigint_handler(*args):
    QtGui.QApplication.quit()


signal.signal(signal.SIGINT, sigint_handler)

# set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(stride * 1000)  # in milliseconds

# Wait until there is enough dat
begsample = -1
while begsample < 0:
    hdr_input = ft_input.getHeader()
    begsample = int(hdr_input.nSamples - window)

# Start
QtGui.QApplication.instance().exec_()
