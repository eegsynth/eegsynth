#!/usr/bin/env python

# This module allows playing back a PepiPiaf CSV file in approximately real-time.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2023 EEGsynth project
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
import pandas

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
    global filename, f, d, c, stepsize, sample

    # get the options from the configuration file
    speed = patch.getfloat('playback', 'speed', default=1.0)
    filename = patch.getstring('playback', 'file')

    monitor.info("Reading data from " + filename)

    d = pandas.read_csv(filename, comment='#')
    # the first few rows tend to be invalid
    d = d[d.month>0]
    c = d.columns

    days_per_month = 365.25/12
    hours_per_day = 24
    minutes_per_hour = 60
    seconds_per_minute = 60

    # compute the time in seconds
    t = (((d.month*days_per_month + d.day)*hours_per_day + d.hour)*minutes_per_hour + d.minutes)*seconds_per_minute
    # estimate the stepsize as the time between rows
    stepsize = np.mean(np.diff(t.to_numpy()))
    stepsize /= speed

    # it is easier to continue with a numpy array
    d = d.to_numpy()
    sample = 0

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global filename, f, d, c, stepsize, elapsed, naptime, sample

    if sample > len(d) - 1:
        monitor.info("End of file reached, jumping back to start")
        sample = 0

    if patch.getint('playback', 'rewind', default=0):
        monitor.info("Rewind pressed, jumping back to start of file")
        sample = 0

    if not patch.getint('playback', 'play', default=1):
        monitor.info("Stopped")
        time.sleep(0.1)
        return

    if patch.getint('playback', 'pause', default=0):
        monitor.info("Paused")
        time.sleep(0.1)
        return

    monitor.debug("Playing sample", sample)
    
    for colindx, colname in enumerate(c):
            key = patch.getstring('output', 'prefix') + '.' + colname
            val = d[sample, colindx]
            patch.setvalue(key, val)
            monitor.update(key, val)

    # increment the sample for teh next time    
    sample += 1


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, stepsize, elapsed, naptime
    while True:
        # measure the time to correct for the slip
        start = time.time()

        monitor.loop()
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


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()

