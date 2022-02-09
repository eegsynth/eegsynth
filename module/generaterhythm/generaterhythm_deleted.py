#!/usr/bin/env python

# Generatetrigger generates triggers at random intervals and sends them to Redis
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019 EEGsynth project
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
import numpy as np
import os
import redis
import sys
import time
import threading
# from numpy import random
from scipy.stats import binom, norm

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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

class ResetThread(threading.Thread):
    def __init__(self, redischannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        global patternreset
        monitor.debug('Reset Thread Running')

        pubsub = r.pubsub()
        # this message unblocks the Redis listen command
        pubsub.subscribe('THREAD_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)

        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    with lock:
                        if patch.getfloat('buttons', 'patternreset') == 1:
                            patternreset = 1

def burst(value=0.2):
    key = patch.getstring('output', 'prefix') + '.note'
    with lock:
        patch.setvalue(key, value)
        monitor.debug('BURST')

def trigger(send=True):
    global patch, t, lock, baserate, burstprob, burstrate, basestd, burststd, triggerindx, jitterlist, valuelist
    global burstlist, val, burstindx, baselock, burstlock, pitchlock, patternlength,  patternreset
    global this, resetpressed, dt, burstprobnext, t1, t2, tcomp, changerate

    if send:
        # send the current trigger if there is a value
        key = patch.getstring('output', 'prefix') + '.note'
        with lock:
            patch.setvalue(key, val)

    with lock:

        if patternreset:
            valuelist  = []
            jitterlist = []
            burstlist = []
            triggerindx = 0
            patternreset = 0
            monitor.debug('Resetting pattern')

        # maintain only length of pattern
        if len(valuelist) > patternlength:
            valuelist = valuelist[-patternlength:]
            jitterlist = jitterlist[-patternlength:]
            burstlist = burstlist[-patternlength:]

        # maintain at end of pattern, or loop around
        if triggerindx > patternlength-1:
            if baselock:
                triggerindx = 0
            else:
                triggerindx = patternlength

        if triggerindx > len(valuelist)-1:
            if np.random.random() < burstprob:
                # add n number of triggers from normal distribution
                nrtriggers = binom.rvs(n=5, p=burstprobnext, size=1) + 1
                burstlist.append(nrtriggers[0])
                jitter = norm.rvs(size=nrtriggers[0], loc=0, scale=0.25)
                jitterlist.append(jitter)
                valuelist.append(np.random.random())
            else:
                burstlist.append(0)
                jitter = norm.rvs(size=1, loc=0, scale=0.25)
                jitterlist.append(jitter[0])
                valuelist.append(np.random.random())
        else:
            monitor.debug('changerate:', changerate)

            if np.random.random() < changerate:
                monitor.debug('WANT TO CHANGE')

                if np.random.random() < burstprob:
                    monitor.debug('CHANGING BURST')
                    # add n number of triggers from normal distribution
                    nrtriggers = binom.rvs(n=5, p=burstprobnext, size=1) + 1
                    burstlist[triggerindx] = nrtriggers[0]
                    jitter = norm.rvs(size=nrtriggers[0], loc=0, scale=0.25)
                    jitterlist[triggerindx] = jitter
                    valuelist[triggerindx] = np.random.random()
                else:
                    monitor.debug('CHANGING NORMAL')

                    burstlist[triggerindx] = 0
                    jitter = norm.rvs(size=1, loc=0, scale=0.25)
                    jitterlist[triggerindx] = jitter[0]
                    valuelist[triggerindx] = np.random.random()

        # get pitch value for next hit
        val = valuelist[triggerindx]

        # get dt for next hit
        t2 = time.time()
        tdiff = t2-t1
        t1 = time.time()
        monitor.debug('Time difference: %f' % (tdiff-dt))
        tcomp = 0.9 * tcomp + 0.1 * (tdiff-dt)
        if burstlist[triggerindx] == 0:
            dt = min(max((60.0 / baserate) + (60.0 / baserate) * jitterlist[triggerindx] * basestd - tcomp, 0.05), 5)
            t = threading.Timer(dt, trigger)
            t.start()
        else:
            dt = min(max((60.0 / baserate) + (60.0 / baserate) * jitterlist[triggerindx][0] * basestd - tcomp, 0.05), 5)
            # first start regular
            t = threading.Timer(dt, trigger)
            t.start()

            # then add burst
            monitor.debug('burstlist', burstlist[triggerindx])
            burstnr = int(min(burstlist[triggerindx], burstrate-1))
            dt_reg = min(max((60.0 / baserate) - tcomp, 0.05), 5)
            divtime = (60.0 / baserate / int(burstrate))

            for i in range(1, burstnr+1):
                dt_burst = dt_reg + (i * divtime) + divtime * jitterlist[triggerindx][i-1] * burststd
                b = threading.Timer(dt_burst, burst, [val])
                b.start()

        # advance counters
        triggerindx += 1
        monitor.debug('6) dt: %f, val: %f, listlength:%d, burstlistlength:%d, triggerind:%d, burstindex:%d, patternlength:%d' % (dt, val, len(valuelist), len(burstlist), triggerindx, burstindx, patternlength))


def _setup():
    """Initialize the module
    This adds a set of global variables
    """
    global parser, args, config, r, response, patch

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'),
                        help="name of the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0,
                              charset='utf-8', decode_responses=True)
        response = r.client_list()
    except redis.ConnectionError:
        raise RuntimeError("cannot connect to Redis server")

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    """Start the module
    This uses the global variables from setup and adds a set of global variables
    """
    global parser, args, config, r, response, patch, name
    global monitor, debug, scale_baserate, offset_baserate, baserate, lock, t
    global burstprob, burstrate, scale_burstprob, offset_burstprob, scale_burstrate, offset_burstrate
    global triggerindx, jitterlist, valuelist, burstlist, val, baselock, burstlock, pitchlock, patternlength, basestd, burststd, patternreset
    global scale_patternlength, scale_basestd, scale_burststd, offset_patternlength, offset_basestd, offset_burststd, burstindx
    global resetpressed, this, dt, burstprobnext, scale_burstprobnext, offset_burstprobnext, t1, t2, tcomp, changerate, scale_changerate, offset_changerate



    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    # the scale and offset are used to map the Redis values to internal values
    scale_baserate = patch.getfloat('scale', 'baserate', default=240)
    offset_baserate = patch.getfloat('offset', 'baserate', default=0)
    baserate = patch.getfloat('interval', 'baserate', default=1)
    baserate = EEGsynth.rescale(baserate, slope=scale_baserate, offset=offset_baserate)

    scale_burstprob = patch.getfloat('scale', 'burstprob', default=1)
    offset_burstprob = patch.getfloat('offset', 'burstprob', default=0)
    burstprob = patch.getfloat('interval', 'burstprob', default=0)
    burstprob = EEGsynth.rescale(burstprob, slope=scale_burstprob, offset=offset_burstprob)

    scale_burstprobnext = patch.getfloat('scale', 'burstprobnext', default=0.5)
    offset_burstprobnext = patch.getfloat('offset', 'burstprobnext', default=0)
    burstprobnext = patch.getfloat('interval', 'burstprobnext', default=0)
    burstprobnext = EEGsynth.rescale(burstprobnext, slope=scale_burstprobnext, offset=offset_burstprobnext)

    scale_burstrate = patch.getfloat('scale', 'burstrate', default=240)
    offset_burstrate = patch.getfloat('offset', 'burstrate', default=0)
    burstrate = patch.getfloat('interval', 'burstrate', default=60)
    burstrate = EEGsynth.rescale(burstrate, slope=scale_burstrate, offset=offset_burstrate)

    scale_patternlength = patch.getfloat('scale', 'patternlength', default=31)
    offset_patternlength = patch.getfloat('offset', 'patternlength', default=1)
    patternlength = patch.getfloat('interval', 'patternlength', default=1)
    patternlength = int(EEGsynth.rescale(patternlength, slope=scale_patternlength, offset=offset_patternlength))

    scale_basestd = patch.getfloat('scale', 'basestd', default=1)
    offset_basestd = patch.getfloat('offset', 'basestd', default=1)
    basestd = patch.getfloat('interval', 'basestd', default=0)
    basestd = EEGsynth.rescale(basestd, slope=scale_basestd, offset=offset_basestd)

    scale_changerate = patch.getfloat('scale', 'changerate', default=1)
    offset_changerate = patch.getfloat('offset', 'changerate', default=0)
    changerate = patch.getfloat('interval', 'changerate', default=0)
    changerate = EEGsynth.rescale(changerate, slope=scale_changerate, offset=offset_changerate)

    scale_burststd = patch.getfloat('scale', 'burststd', default=1)
    offset_burststd = patch.getfloat('offset', 'burststd', default=1)
    burststd = patch.getfloat('interval', 'burststd', default=0)
    burststd = EEGsynth.rescale(burststd, slope=scale_burststd, offset=offset_burststd)

    pitchlock = patch.getint('buttons', 'pitchlock', default=1)
    baselock = patch.getint('buttons', 'baselock', default=1)
    burstlock = patch.getint('buttons', 'burstlock', default=0)

    # start with empty list and index = 0, list will be created in loop
    triggerindx = 0
    jitterlist = []
    valuelist = []
    burstlist = []
    burstindx = 0
    val = 0
    dt = 1
    patternreset = 0
    t1 = time.time()
    t2 = time.time()
    tcomp = 0

    # this is to prevent the trigger function from accessing the parameters while they are being updated
    lock = threading.Lock()

    # make an initial timer object, this is needed in case parameters are updated prior to the execution of the first trigger
    t = threading.Timer(0, None)

    # create the threads that deal with the triggers
    resetkey = config['buttons']['patternreset']
    this = ResetThread(resetkey)
    this.start()

    # start the chain of triggers, the first one does not have to be sent
    trigger(send=False)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global parser, args, config, r, response
    global patch, monitor, debug, scale_baserate, offset_baserate, baserate, spread, lock, t
    global change
    global burstprob, burstrate, scale_burstprob, scale_burstrate, offset_burstprob, offset_burstrate
    global burstprob, scale_burstprob, offset_burstprob
    global baselock, burstlock, pitchlock, patternlength, scale_patternlength, basestd, burststd, patternreset
    global scale_basestd, scale_burststd, offset_patternlength, offset_basestd, offset_burststd
    global resetpressed, dt,  burstprobnext, scale_burstprobnext, offset_burstprobnext, t1, t2, tcomp, changerate, scale_changerate, offset_changerate


    with lock:
        # the scale and offset are used to map the Redis values to internal values
        scale_baserate = patch.getfloat('scale', 'baserate', default=240)
        offset_baserate = patch.getfloat('offset', 'baserate', default=0)
        baserate = patch.getfloat('interval', 'baserate', default=1)
        baserate = EEGsynth.rescale(baserate, slope=scale_baserate, offset=offset_baserate)

        scale_burstprob = patch.getfloat('scale', 'burstprob', default=1)
        offset_burstprob = patch.getfloat('offset', 'burstprob', default=0)
        burstprob = patch.getfloat('interval', 'burstprob', default=0)
        burstprob = EEGsynth.rescale(burstprob, slope=scale_burstprob, offset=offset_burstprob)

        scale_burstprobnext = patch.getfloat('scale', 'burstprobnext', default=0.5)
        offset_burstprobnext = patch.getfloat('offset', 'burstprobnext', default=0)
        burstprobnext = patch.getfloat('interval', 'burstprobnext', default=0)
        burstprobnext = EEGsynth.rescale(burstprobnext, slope=scale_burstprobnext, offset=offset_burstprobnext)

        scale_burstrate = patch.getfloat('scale', 'burstrate', default=240)
        offset_burstrate = patch.getfloat('offset', 'burstrate', default=0)
        burstrate = patch.getfloat('interval', 'burstrate', default=60)
        burstrate = EEGsynth.rescale(burstrate, slope=scale_burstrate, offset=offset_burstrate)

        scale_patternlength = patch.getfloat('scale', 'patternlength', default=31)
        offset_patternlength = patch.getfloat('offset', 'patternlength', default=1)
        patternlength = patch.getfloat('interval', 'patternlength', default=1)
        patternlength = int(EEGsynth.rescale(patternlength, slope=scale_patternlength, offset=offset_patternlength))

        scale_basestd = patch.getfloat('scale', 'basestd', default=1)
        offset_basestd = patch.getfloat('offset', 'basestd', default=1)
        basestd = patch.getfloat('interval', 'basestd', default=0)
        basestd = EEGsynth.rescale(basestd, slope=scale_basestd, offset=offset_basestd)

        scale_changerate = patch.getfloat('scale', 'changerate', default=1)
        offset_changerate = patch.getfloat('offset', 'changerate', default=0)
        changerate = patch.getfloat('interval', 'changerate', default=0)
        changerate = EEGsynth.rescale(changerate, slope=scale_changerate, offset=offset_changerate)

        scale_burststd = patch.getfloat('scale', 'burststd', default=1)
        offset_burststd = patch.getfloat('offset', 'burststd', default=1)
        burststd = patch.getfloat('interval', 'burststd', default=0)
        burststd = EEGsynth.rescale(burststd, slope=scale_burststd, offset=offset_burststd)

        pitchlock = patch.getint('buttons', 'pitchlock', default=1)
        baselock = patch.getint('buttons', 'baselock', default=1)
        burstlock = patch.getint('buttons', 'burstlock', default=0)


    change = monitor.update('baserate', baserate)
    change = monitor.update('burstprob', burstprob)
    change = monitor.update('burstrate', burstrate)
    change = monitor.update('patternlength', patternlength)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_forever():
    """Run the main loop forever
    """
    global monitor, patch
    while True:
        # monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt
    """
    monitor.success('Closing threads')
    this.stop()
    r.publish('THREAD_UNBLOCK', 1)
    this.join()
    sys.exit()

if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except:
        _stop()
