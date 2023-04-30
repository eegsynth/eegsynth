#!/usr/bin/env python

# Csp calculates a common spatial pattern from a series of files and outputs
# them as Redis values for use as a spatial filter (montage) in preprocessing
# Currently only a two-state solution is supported.
#
# The Python implementation of the CSP is a copy of:
# https://github.com/spolsley/common-spatial-patterns/blob/master/CSP.py
# See README.MD for reference article
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2022 EEGsynth project
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

import numpy as np
import os
import sys
import time
import wave
import struct
import glob
import scipy.linalg as la
import scipy.signal as signal
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable # part of matplotlib

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth
import FieldTrip
import EDF


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global stepsize, filename, fileformat
    global data_A, filepath_A
    global data_B, filepath_B
    global scale_lowpass, scale_highpass, scale_notchfilter, offset_lowpass, offset_highpass, offset_notchfilter, scale_filtorder, scale_notchquality, offset_filtorder, offset_notchquality
    global lpfreq, hpfreq, filtorder, hp, lp
    global filenames, indx, filenr, filename, f, data, chanindx, filters, cmap, fig, axes, i, ax, im, divider, cax, prefix, icomp, comp, iweight, weight, key

    # get the options from the configuration file
    stepsize   = patch.getfloat('general', 'delay')
    filepath_A = patch.getstring('data', 'conditionA')
    filepath_B = patch.getstring('data', 'conditionB')
    fileformat = patch.getstring('data', 'format')

    if fileformat is None:
        # determine the file format from the file name
        name, ext = os.path.splitext(filepath_A)
        fileformat = ext[1:]

    hpfreq = patch.getfloat('processing', 'highpassfilter', default=None)
    lpfreq = patch.getfloat('processing', 'lowpassfilter', default=None)
    filtorder = patch.getfloat('processing', 'filtorder', default=9)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global H, A
    global D, stepsize
    global data_A, filepath_A
    global data_B, filepath_B
    global scale_lowpass, scale_highpass, scale_notchfilter, offset_lowpass, offset_highpass, offset_notchfilter, scale_filtorder, scale_notchquality, offset_filtorder, offset_notchquality
    global nChannels, fSample, nSamples, labels
    global lpfreq, hpfreq, filtorder, hp, lp
    global filenames, indx, filenr, filename, f, data, chanindx, filters, cmap, fig, axes, i, ax, im, divider, cax, prefix, icomp, comp, iweight, weight, key

    if fileformat == 'edf':

        filenames = glob.glob(filepath_A) + glob.glob(filepath_B)
        indx      = np.concatenate(   (  np.zeros(len(glob.glob(filepath_A))), np.ones(len(glob.glob(filepath_B)))  )  )
        monitor.info('Found %d files for condition A, and %d files for condition B' % (len(glob.glob(filepath_A)), len(glob.glob(filepath_B))))

        # get info about available recordings
        nChannels   = []
        fSample     = []
        nSamples    = []
        for filenr, filename in enumerate(filenames):
            f = EDF.EDFReader()
            f.open(filename)

            if any(np.diff(f.getSignalFreqs())):
                raise AssertionError('unequal SignalFreqs in recording')
            if any(np.diff(f.getNSamples())):
                raise AssertionError('unequal NSamples in recording')

            nChannels.append(len(f.getSignalFreqs()))
            nSamples.append(f.getNSamples()[0])
            fSample.append(f.getSignalFreqs()[0])
            monitor.info('%d channels with %d samples at %d Hz found in: %s' % (nChannels[-1], nSamples[-1], fSample[-1], filename))
            f.close()

        if any(np.diff(nChannels)):
            raise AssertionError('Different number of channels in files!')

        if any(np.diff(fSample)):
            raise AssertionError('Different samplerates in files!')

        if any(np.diff(nSamples)):
            monitor.info('Different number of samples in files, will only read the minimum of (%d samples)' % (min(nSamples)))

        # read condition A
        data = np.ndarray(shape=(len(filenames), nChannels[0], min(nSamples)), dtype=np.float32)
        for filenr, filename in enumerate(filenames):
            with open(filename, 'r') as f:
                monitor.info('Adding condition %d: %s' % (indx[filenr], filename))
                f = EDF.EDFReader()
                f.open(filename)

                # read all the data from the file
                for chanindx in range(nChannels[0]):
                    data[filenr][chanindx, :] = f.readSignal(chanindx)[0:min(nSamples)]
                    data[filenr, chanindx, :] = data[filenr, chanindx, :] - data[filenr, chanindx, :].mean(axis = 0)

                    if hpfreq:
                        monitor.debug('Applying highpassfilter at %.1f Hertz' % (hpfreq))
                        data[filenr, chanindx, :] = EEGsynth.butter_highpass_filter(data[filenr, chanindx, :], hpfreq, int(fSample[0]), filtorder)

                    if lpfreq:
                        monitor.debug('Applying lowpassfilter at %.1f Hertz' % (lpfreq))
                        data[filenr, chanindx, :] = EEGsynth.butter_lowpass_filter(data[filenr, chanindx, :], lpfreq, int(fSample[0]), filtorder)

                f.close()

    else:
        raise NotImplementedError('unsupported file format')

    # plot timecourses for debugging
    if patch.getint('general', 'debug', default=1) == 3:
        for filenr, filename in enumerate(filenames):
            fig = plt.figure(filenr+1)
            for chanindx in range(nChannels[0]):
                print('file nr. %d channel nr. %d' % (filenr, chanindx))
                plt.subplot(8, 1, chanindx+1)
                plt.plot(data[filenr][chanindx, :])
            plt.show()

    # calculate CSP
    filters = CSP(data[indx==0], data[indx==1])

    # plot CSP when debugging
    if patch.getint('general', 'debug', default=1) == 3:
        cmap = cm.coolwarm
        fig, axes = plt.subplots(1,2, figsize=(8,8))
        for i, ax in enumerate(axes.flat):
            im = ax.imshow(filters[i], norm=colors.CenteredNorm(0), cmap = cmap)
            # pc = ax.imshow(filters[i])
            # plt.colorbar(pc, ax=ax)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            plt.colorbar(im, cax=cax)
            # pc = ax.pcolormesh(filters[i], norm=colors.CenteredNorm(), cmap=cmap)
            # fig.colorbar(pc, ax=ax2)
            ax.set_title('CSP %d' % i)
        plt.show()

    # only write first filter (only 2 state solution)
    prefix = 'csp'
    for icomp, comp in enumerate(filters[0]):
        for iweight, weight in enumerate(filters[0][icomp, :]):
            key = '{prefix}.{icomp}.{iweight}'.format(prefix=prefix, icomp=icomp+1, iweight=iweight+1)
            patch.setvalue(key, float(weight))
            monitor.debug(key + ' = ' + str(weight))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, stepsize
    while True:
        # measure the time to correct for the slip
        start = time.time()

        monitor.loop()
        enabled = patch.getint('processing', 'enable', default=None)
        if enabled:
            _loop_once()

        elapsed = time.time() - start
        naptime = stepsize - elapsed
        if naptime > 0:
            # this approximates the real time streaming speed
            time.sleep(naptime)

def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    pass


def CSP(*tasks):
    if len(tasks) < 2:
        print("Must have at least 2 tasks for filtering.")
        return (None,) * len(tasks)
    else:
        filters = ()
        # CSP algorithm
        # For each task x, find the mean variances Rx and not_Rx, which will be used to compute spatial filter SFx
        iterator = range(0,len(tasks))
        for x in iterator:
            # Find Rx
            Rx = covarianceMatrix(tasks[x][0])
            for t in range(1,len(tasks[x])):
                Rx += covarianceMatrix(tasks[x][t])
            Rx = Rx / len(tasks[x])

            # Find not_Rx
            count = 0
            not_Rx = Rx * 0
            for not_x in [element for element in iterator if element != x]:
                for t in range(0,len(tasks[not_x])):
                    not_Rx += covarianceMatrix(tasks[not_x][t])
                    count += 1
            not_Rx = not_Rx / count

			# Find the spatial filter SFx
            SFx = spatialFilter(Rx,not_Rx)
            filters += (SFx,)
			# Special case: only two tasks, no need to compute any more mean variances
            if len(tasks) == 2:
                filters += (spatialFilter(not_Rx,Rx),)
                break
        return filters


# covarianceMatrix takes a matrix A and returns the covariance matrix, scaled by the variance
def covarianceMatrix(A):
    Ca = np.dot(A,np.transpose(A))/np.trace(np.dot(A,np.transpose(A)))
    return Ca


# spatialFilter returns the spatial filter SFa for mean covariance matrices Ra and Rb
def spatialFilter(Ra,Rb):
    R = Ra + Rb
    E,U = la.eig(R)

    # CSP requires the eigenvalues E and eigenvector U be sorted in descending order
    ord = np.argsort(E)
    ord = ord[::-1] # argsort gives ascending order, flip to get descending
    E = E[ord]
    U = U[:,ord]

	# Find the whitening transformation matrix
    P = np.dot(np.sqrt(la.inv(np.diag(E))),np.transpose(U))

	# The mean covariance matrices may now be transformed
    Sa = np.dot(P,np.dot(Ra,np.transpose(P)))
    Sb = np.dot(P,np.dot(Rb,np.transpose(P)))

	# Find and sort the generalized eigenvalues and eigenvector
    E1,U1 = la.eig(Sa,Sb)
    ord1 = np.argsort(E1)
    ord1 = ord1[::-1]
    E1 = E1[ord1]
    U1 = U1[:,ord1]

    # The projection matrix (the spatial filter) may now be obtained
    SFa = np.dot(np.transpose(U1),P)

    return SFa.astype(np.float32)


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
