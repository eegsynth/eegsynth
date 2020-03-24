#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
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

import configparser
import argparse
import os
import redis
import sys
import time
import numpy as np
from sklearn.preprocessing import QuantileTransformer
import warnings
warnings.simplefilter("ignore", UserWarning)

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
import EEGsynth

def baseline_norm(bl_values, datum, qt):
    bl_corrected_datum = qt.fit_transform(np.append(bl_values, datum).reshape(-1,1))[-1]
    return bl_corrected_datum

def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug, duration, delay, suffixe, list_input, key_name, red_name, baseline_computed, bl_values, qt
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
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
    monitor = EEGsynth.monitor()

    # get the options from the configuration file
    debug = patch.getint('general','debug')
    duration = patch.getint('general', 'duration')
    delay = patch.getfloat('general', 'delay')

    # get suffixe string from the configuration file
    suffixe = patch.getstring('output', 'suffixe')

    # keys should be present in the input section of the *.ini file
    list_input  = config.items('input')

    key_name = [] # the key name that matches in the input
    red_name = [] # the key name in Redis
    for i in range(len(list_input)):
        key_name.append(list_input[i][0])
        red_name.append(list_input[i][1])

    bl_values = dict()
    for key in red_name:
        bl_values[key] = []

    qt = QuantileTransformer(n_quantiles=1000, output_distribution='normal')
    baseline_computed = False


def _loop_once():
    global parser, args, config, r, response, patch, monitor, debug, duration, delay, suffixe, list_input, key_name, red_name, baseline_computed, bl_values, qt
    monitor.loop()
    time.sleep(delay)

    if baseline_computed == False:
        for key1, key2 in zip(key_name,red_name):
            val = patch.getfloat('input', key1, multiple=True)
            bl_values[key2].append(val)
            if len(bl_values[key2]) == int(duration/delay): # Check if enough values are accumulated
                baseline_computed = True # If True, stop accumulating
    else:
        for key1,key2 in zip(key_name,red_name):
            val = patch.getfloat('input', key1, multiple=True)
            if any(item is None for item in val):
                # the control value is not present in redis, skip it
                continue
            else:
                val = [float(x) for x in val]

            val_norm = baseline_norm(bl_values[key2], val, qt)
            redis_key = key2 + '.' + suffixe
            patch.setvalue(redis_key, np.float(val_norm))

def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


if __name__ == '__main__':
    _setup()
    input('Press enter to start recording baseline for {} seconds.'.format(str(duration)))
    _loop_forever()
