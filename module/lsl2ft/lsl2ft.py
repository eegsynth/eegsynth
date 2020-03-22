#!/usr/bin/env python

# Lsl2ft reads data from an LSL stream and writes it to a FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019-2020 EEGsynth project
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
import pylsl as lsl

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
import FieldTrip
import EEGsynth


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
    global monitor, timeout, lsl_name, lsl_type, ft_host, ft_port, ft_output, start, selected, streams, stream, inlet, type, source_id, match, lsl_id, channel_count, channel_format, nominal_srate, samples, blocksize

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    timeout = patch.getfloat('lsl', 'timeout', default=30)
    lsl_name = patch.getstring('lsl', 'name')
    lsl_type = patch.getstring('lsl', 'type')

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.info("Connected to output FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")

    monitor.success("looking for an LSL stream...")
    start = time.time()
    selected = []
    while len(selected) < 1:
        if (time.time() - start) > timeout:
            monitor.error("Error: timeout while waiting for LSL stream")
            raise SystemExit

        # find the desired stream on the lab network
        streams = lsl.resolve_streams()
        for stream in streams:
            inlet = lsl.StreamInlet(stream)
            name = inlet.info().name()
            type = inlet.info().type()
            source_id = inlet.info().source_id()
            # determine whether this stream should be further processed
            match = True
            if len(lsl_name):
                match = match and lsl_name == name
            if len(lsl_type):
                match = match and lsl_type == type
            if match:
                # select this stream for further processing
                selected.append(stream)
                monitor.success('-------- STREAM(*) ------')
            else:
                monitor.success('-------- STREAM ---------')
            monitor.info("name = " + name)
            monitor.info("type = " + type)
        monitor.success('-------------------------')

    # create a new inlet from the first (and hopefully only) selected stream
    inlet = lsl.StreamInlet(selected[0])

    # give some feedback
    lsl_name = inlet.info().name()
    lsl_type = inlet.info().type()
    lsl_id = inlet.info().source_id()
    monitor.success('connected to LSL stream %s (type = %s, id = %s)' % (lsl_name, lsl_type, lsl_id))

    channel_count = inlet.info().channel_count()
    channel_format = inlet.info().channel_format()
    nominal_srate = inlet.info().nominal_srate()

    ft_output.putHeader(channel_count, nominal_srate, FieldTrip.DATATYPE_FLOAT32)

    # this is used for feedback
    samples = 0
    blocksize = 1

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, name
    global monitor, timeout, lsl_name, lsl_type, ft_host, ft_port, ft_output, start, selected, streams, stream, inlet, type, source_id, match, lsl_id, channel_count, channel_format, nominal_srate, samples, blocksize

    monitor.loop()

    chunk, timestamps = inlet.pull_chunk()
    if timestamps:
        dat = np.asarray(chunk, dtype=np.float32)
        ft_output.putData(dat)
        blocksize = dat.shape[0]
        samples += blocksize
        monitor.update('samples', samples)
    else:
        # wait for a short time before trying again
        # this prevents the polling from clogging the CPU to 100%
        time.sleep(0.1 * blocksize / nominal_srate)


def _loop_forever():
    '''Run the main loop forever
    '''
    while True:
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, ft_output

    ft_output.disconnect()
    monitor.success('Disconnected from output FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    _loop_forever()
