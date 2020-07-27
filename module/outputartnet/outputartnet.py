#!/usr/bin/env python

# Outputartnet sends Redis data according to the artnet protocol
#
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

import configparser
import argparse
import os
import redis
import serial
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
import ArtNet


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch

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

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, name
    global monitor, debug, address, artnet, dmxsize, dmxframe, prevtime

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

    # get the options from the configuration file
    debug = patch.getint('general','debug')

    # prepare the data for a single universe
    address = [0, 0, patch.getint('artnet','universe')]
    artnet = ArtNet.ArtNet(ip=patch.getstring('artnet','broadcast'), port=patch.getint('artnet','port'))

    # determine the size of the universe
    dmxsize = 0
    chanlist, chanvals = list(map(list, list(zip(*config.items('input')))))
    for chanindx in range(0, 512):
        chanstr = "channel%03d" % (chanindx + 1)
        if chanstr in chanlist:
            # the last channel determines the size
            dmxsize = chanindx + 1

    # FIXME the artnet code fails if the size is smaller than 512
    dmxsize = 512
    monitor.info("universe size = %d" % dmxsize)

    # make an empty frame
    dmxframe = [0] * dmxsize
    # blank out
    artnet.broadcastDMX(dmxframe, address)

    # keep a timer to send a packet every now and then
    prevtime = time.time()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch
    global monitor, debug, address, artnet, dmxsize, dmxframe, prevtime
    global update, chanindx, chanstr, chanval, scale, offset

    update = False

    # loop over the control values, these are 1-offset in the ini file
    for chanindx in range(0, dmxsize):
        chanstr = "channel%03d" % (chanindx + 1)
        # this returns None when the channel is not present
        chanval = patch.getfloat('input', chanstr)

        if chanval == None:
            # the value is not present in Redis, skip it
            continue

        # the scale and offset options are channel specific
        scale = patch.getfloat('scale', chanstr, default=255)
        offset = patch.getfloat('offset', chanstr, default=0)
        # apply the scale and offset
        chanval = EEGsynth.rescale(chanval, slope=scale, offset=offset)
        # ensure that it is within limits
        chanval = EEGsynth.limit(chanval, lo=0, hi=255)
        chanval = int(chanval)

        # only update if the value has changed
        if dmxframe[chanindx] != chanval:
            monitor.info("DMX channel%03d = %g" % (chanindx, chanval))
            dmxframe[chanindx] = chanval
            update = True

    if update:
        artnet.broadcastDMX(dmxframe, address)
        prevtime = time.time()

    elif (time.time() - prevtime) > 0.5:
        # send a maintenance frame every 0.5 seconds
        artnet.broadcastDMX(dmxframe, address)
        prevtime = time.time()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, artnet
    monitor.success("Closing module...")
    # blank out
    dmxframe = [0] * 512
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.broadcastDMX(dmxframe,address)
    time.sleep(0.1) # this seems to take some time
    artnet.close()
    sys.exit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
