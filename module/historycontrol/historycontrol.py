#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2022 EEGsynth project
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std
import numpy as np
import os
import sys
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__=='__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path,'../../lib'))
import EEGsynth


def mad(arr, axis=None):
    # see https://en.wikipedia.org/wiki/Median_absolute_deviation
    if axis==1:
        val = np.apply_along_axis(mad, 1, arr)
    else:
        val = np.nanmedian(np.abs(arr - np.nanmedian(arr)))
    return val


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
    global inputlist, enable, stepsize, window, metrics_iqr, metrics_mad, metrics_max, metrics_max_att, metrics_mean, metrics_median, metrics_min, metrics_min_att, metrics_p03, metrics_p16, metrics_p84, metrics_p97, metrics_range, metrics_std, numchannel, numhistory, historic_data, historic_stat

    # get the options from the configuration file
    inputlist   = patch.getstring('input', 'channels', multiple=True)
    enable      = patch.getint('history', 'enable', default=1)
    stepsize    = patch.getfloat('history', 'stepsize')                 # stepize in seconds
    window      = patch.getfloat('history', 'window')                   # length of sliding window in seconds

    metrics_iqr     = patch.getint('metrics', 'iqr',     default=1) != 0
    metrics_mad     = patch.getint('metrics', 'mad',     default=1) != 0
    metrics_max     = patch.getint('metrics', 'max',     default=1) != 0
    metrics_max_att = patch.getint('metrics', 'max_att', default=1) != 0
    metrics_mean    = patch.getint('metrics', 'mean',    default=1) != 0
    metrics_median  = patch.getint('metrics', 'median',  default=1) != 0
    metrics_min     = patch.getint('metrics', 'min',     default=1) != 0
    metrics_min_att = patch.getint('metrics', 'min_att', default=1) != 0
    metrics_p03     = patch.getint('metrics', 'p03',     default=1) != 0
    metrics_p16     = patch.getint('metrics', 'p16',     default=1) != 0
    metrics_p84     = patch.getint('metrics', 'p84',     default=1) != 0
    metrics_p97     = patch.getint('metrics', 'p97',     default=1) != 0
    metrics_range   = patch.getint('metrics', 'range',   default=1) != 0
    metrics_std     = patch.getint('metrics', 'std',     default=1) != 0

    numchannel  = len(inputlist)
    numhistory  = int(round(window/stepsize))

    # this will contain the full list of historic_stat values
    historic_data = np.empty((numchannel, numhistory)) * np.NAN

    # this will contain the statistics of the historic_stat values
    historic_stat = {}

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global inputlist, enable, stepsize, window, metrics_iqr, metrics_mad, metrics_max, metrics_max_att, metrics_mean, metrics_median, metrics_min, metrics_min_att, metrics_p03, metrics_p16, metrics_p84, metrics_p97, metrics_range, metrics_std, numchannel, numhistory, historic_data, historic_stat
    global channel, historic_att, operation, key, val

    # determine whether the historic_data should be updated or not
    enable = patch.getint('history', 'enable', default=1)
    monitor.update("enable", enable)
    if not enable:
        return

    # shift the data to next sample
    historic_data[:, :-1] = historic_data[:, 1:]

    # update with the current data
    for channel in range(numchannel):
        try:
            historic_data[channel, numhistory-1] = float(patch.redis.get(inputlist[channel]))
        except:
            historic_data[channel, numhistory-1] = np.NaN

    if metrics_mean or metrics_max_att or metrics_min_att:
        historic_stat['mean']    = np.nanmean(historic_data, axis=1)
    if metrics_min or metrics_range:
        historic_stat['min']     = np.nanmin(historic_data, axis=1)
    if metrics_max or metrics_range:
        historic_stat['max']     = np.nanmax(historic_data, axis=1)

    # use some robust estimators
    if metrics_median:
        historic_stat['median']  = np.nanmedian(historic_data, axis=1)
    if metrics_mad:
        # see https://en.wikipedia.org/wiki/Median_absolute_deviation
        historic_stat['mad']     = mad(historic_data, axis=1)

    # for a normal distribution the 16th and 84th percentile correspond to the mean plus-minus one standard deviation
    if metrics_p03:
        historic_stat['p03']     = np.percentile(historic_data,  3, axis=1) # mean minus 2x standard deviation
    if metrics_p16 or metrics_iqr:
        historic_stat['p16']     = np.percentile(historic_data, 16, axis=1) # mean minus 1x standard deviation
    if metrics_p84 or metrics_iqr:
        historic_stat['p84']     = np.percentile(historic_data, 84, axis=1) # mean plus 1x standard deviation
    if metrics_p97:
        historic_stat['p97']     = np.percentile(historic_data, 97, axis=1) # mean plus 2x standard deviation

    if metrics_iqr:
        # see https://en.wikipedia.org/wiki/Interquartile_range
        historic_stat['iqr']     = historic_stat['p84'] - historic_stat['p16']

    if metrics_range:
        historic_stat['range']   = historic_stat['max'] - historic_stat['min']
    if metrics_std:
        historic_stat['std']     = np.nanstd(historic_data, axis=1)

    if metrics_max_att or metrics_min_att:
        # Attenuated historic_data over time, so to diminish max/min over time
        # NOTE: There is probably a way to do this without a for-loop:
        historic_att = historic_data
        for channel in range(numchannel):
            historic_att[channel, :] = historic_att[channel, :] - historic_stat['mean'][channel]
            historic_att[channel, :] = historic_att[channel, :] * np.linspace(0, 1, numhistory)
            historic_att[channel, :] = historic_att[channel, :] + historic_stat['mean'][channel]

    if metrics_max_att or metrics_min_att:
        historic_stat['min_att'] = np.nanmin(historic_att, axis=1)
        historic_stat['max_att'] = np.nanmax(historic_att, axis=1)

    for operation in list(historic_stat.keys()):
        for channel in range(numchannel):
            key = inputlist[channel] + "." + operation
            val = historic_stat[operation][channel]
            patch.setvalue(key, val)
            monitor.debug('%s = %g' % (key, val))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, stepize, elapsed, naptime
    while True:
        # measure the time to correct for the slip
        start = time.time()

        monitor.loop()
        _loop_once()

        # correct for the slip
        elapsed = time.time() - start
        naptime = stepsize - elapsed
        if naptime>0:
            time.sleep(naptime)


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    pass


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
