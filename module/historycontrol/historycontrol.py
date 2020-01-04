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

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name)

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
inputlist   = patch.getstring('input', 'channels', multiple=True)
enable      = patch.getint('history', 'enable', default=1)
stepsize    = patch.getfloat('history', 'stepsize')                 # in seconds
window      = patch.getfloat('history', 'window')                   # in seconds

numchannel  = len(inputlist)
numhistory  = int(round(window/stepsize))

# this will contain the full list of historic values
history = np.empty((numchannel, numhistory)) * np.NAN

# this will contain the statistics of the historic values
historic = {}


# see https://en.wikipedia.org/wiki/Median_absolute_deviation
def mad(arr, axis=None):
    if axis==1:
        val = np.apply_along_axis(mad, 1, arr)
    else:
        val = np.nanmedian(np.abs(arr - np.nanmedian(arr)))
    return val


while True:
    monitor.loop()

    # measure the time to correct for the slip
    start = time.time()

    # update the enable status
    prev_enable = enable
    enable = patch.getint('history', 'enable', default=1)

    if enable and prev_enable:
        if debug > 0:
            print("Updating the history")
    elif enable and not prev_enable:
        if debug > 0:
            print("Enabling the updating")
    elif not enable and not prev_enable:
        if debug > 0:
            print("Not updating the history")
    elif not enable and prev_enable:
        if debug > 0:
            print("Disabling the updating")

    if not enable:
        time.sleep(0.1)

    else:
        # shift data to next sample
        history[:, :-1] = history[:, 1:]

        # update with current data
        for channel in range(numchannel):
            history[channel, numhistory-1] = r.get(inputlist[channel])

        # compute some statistics
        historic['mean']    = np.nanmean(history, axis=1)
        historic['std']     = np.nanstd(history, axis=1)
        historic['min']     = np.nanmin(history, axis=1)
        historic['max']     = np.nanmax(history, axis=1)
        historic['range']   = historic['max'] - historic['min']
        # use some robust estimators
        historic['median']  = np.nanmedian(history, axis=1)
        # see https://en.wikipedia.org/wiki/Median_absolute_deviation
        historic['mad']     = mad(history, axis=1)
        # for a normal distribution the 16th and 84th percentile correspond to the mean plus-minus one standard deviation
        historic['p03']     = np.percentile(history,  3, axis=1) # mean minus 2x standard deviation
        historic['p16']     = np.percentile(history, 16, axis=1) # mean minus 1x standard deviation
        historic['p84']     = np.percentile(history, 84, axis=1) # mean plus 1x standard deviation
        historic['p97']     = np.percentile(history, 97, axis=1) # mean plus 2x standard deviation
        # see https://en.wikipedia.org/wiki/Interquartile_range
        historic['iqr']     = historic['p84'] - historic['p16']

        # Attenuated history over time, so to diminish max/min over time
        # NOTE: There is probably a way to do this without a for-loop:
        history_att = history
        for channel in range(numchannel):
            history_att[channel, :] = history_att[channel, :] - historic['mean'][channel]
            history_att[channel, :] = history_att[channel, :] * np.linspace(0, 1, numhistory)
            history_att[channel, :] = history_att[channel, :] + historic['mean'][channel]

        historic['min_att'] = np.nanmin(history_att, axis=1)
        historic['max_att'] = np.nanmax(history_att, axis=1)

        for operation in list(historic.keys()):
            for channel in range(numchannel):
                key = inputlist[channel] + "." + operation
                val = historic[operation][channel]
                patch.setvalue(key, val)
                if debug>1:
                    print('%s = %g' % (key, val))

        elapsed = time.time() - start
        naptime = stepsize - elapsed
        if naptime>0:
            # this approximates the desired update speed
            time.sleep(naptime)
