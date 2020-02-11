#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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
import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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
    global parser, args, config, r, response

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'), help="name of the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0, charset='utf-8', decode_responses=True)
        response = r.client_list()
    except redis.ConnectionError:
        raise RuntimeError("cannot connect to Redis server")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response
    global patch, monitor, debug, inputlist, enable, stepsize, window, numchannel, numhistory, history, historic, metrics_iqr, metrics_mad , metrics_max , metrics_max_att , metrics_mean , metrics_median , metrics_min , metrics_min_att , metrics_p03 , metrics_p16 , metrics_p84 , metrics_p97 , metrics_range , metrics_std

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug       = patch.getint('general', 'debug')
    inputlist   = patch.getstring('input', 'channels', multiple=True)
    enable      = patch.getint('history', 'enable', default=1)
    stepsize    = patch.getfloat('history', 'stepsize')                 # in seconds
    window      = patch.getfloat('history', 'window')                   # in seconds

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

    # this will contain the full list of historic values
    history = np.empty((numchannel, numhistory)) * np.NAN

    # this will contain the statistics of the historic values
    historic = {}

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response
    global patch, monitor, debug, inputlist, enable, stepsize, window, numchannel, numhistory, history, historic, metrics_iqr, metrics_mad , metrics_max , metrics_max_att , metrics_mean , metrics_median , metrics_min , metrics_min_att , metrics_p03 , metrics_p16 , metrics_p84 , metrics_p97 , metrics_range , metrics_std

    monitor.loop()

    # measure the time to correct for the slip
    start = time.time()

    # update the enable status
    prev_enable = enable
    enable = patch.getint('history', 'enable', default=1)

    if enable and prev_enable:
        monitor.info("Updating the history")
    elif enable and not prev_enable:
        monitor.info("Enabling the updating")
    elif not enable and not prev_enable:
        monitor.info("Not updating the history")
    elif not enable and prev_enable:
        monitor.info("Disabling the updating")

    if not enable:
        time.sleep(0.1)

    else:
        # shift data to next sample
        history[:, :-1] = history[:, 1:]

        # update with current data
        for channel in range(numchannel):
            history[channel, numhistory-1] = r.get(inputlist[channel])

        if metrics_mean or metrics_max_att or metrics_min_att:
            historic['mean']    = np.nanmean(history, axis=1)
        if metrics_min or metrics_range:
            historic['min']     = np.nanmin(history, axis=1)
        if metrics_max or metrics_range:
            historic['max']     = np.nanmax(history, axis=1)

        # use some robust estimators
        if metrics_median:
            historic['median']  = np.nanmedian(history, axis=1)
        if metrics_mad:
            # see https://en.wikipedia.org/wiki/Median_absolute_deviation
            historic['mad']     = mad(history, axis=1)

        # for a normal distribution the 16th and 84th percentile correspond to the mean plus-minus one standard deviation
        if metrics_p03:
            historic['p03']     = np.percentile(history,  3, axis=1) # mean minus 2x standard deviation
        if metrics_p16 or metrics_iqr:
            historic['p16']     = np.percentile(history, 16, axis=1) # mean minus 1x standard deviation
        if metrics_p84 or metrics_iqr:
            historic['p84']     = np.percentile(history, 84, axis=1) # mean plus 1x standard deviation
        if metrics_p97:
            historic['p97']     = np.percentile(history, 97, axis=1) # mean plus 2x standard deviation

        if metrics_iqr:
            # see https://en.wikipedia.org/wiki/Interquartile_range
            historic['iqr']     = historic['p84'] - historic['p16']

        if metrics_range:
            historic['range']   = historic['max'] - historic['min']
        if metrics_std:
            historic['std']     = np.nanstd(history, axis=1)

        if metrics_max_att or metrics_min_att:
            # Attenuated history over time, so to diminish max/min over time
            # NOTE: There is probably a way to do this without a for-loop:
            history_att = history
            for channel in range(numchannel):
                history_att[channel, :] = history_att[channel, :] - historic['mean'][channel]
                history_att[channel, :] = history_att[channel, :] * np.linspace(0, 1, numhistory)
                history_att[channel, :] = history_att[channel, :] + historic['mean'][channel]

        if metrics_max_att or metrics_min_att:
            historic['min_att'] = np.nanmin(history_att, axis=1)
            historic['max_att'] = np.nanmax(history_att, axis=1)

        for operation in list(historic.keys()):
            for channel in range(numchannel):
                key = inputlist[channel] + "." + operation
                val = historic[operation][channel]
                patch.setvalue(key, val)
                monitor.debug('%s = %g' % (key, val))

        elapsed = time.time() - start
        naptime = stepsize - elapsed
        if naptime>0:
            # this approximates the desired update speed
            time.sleep(naptime)


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    pass


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
