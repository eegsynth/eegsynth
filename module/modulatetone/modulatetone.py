#!/usr/bin/env python

# This module reads constol signals from Redis and uses them to play a mixture of modulated tones over audio
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

import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time
import signal
import threading
import pyaudio

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


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, audiochannel, tone):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.audiochannel = audiochannel
        self.tone = tone
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        global frequencies, control, channame
        pubsub = r.pubsub()
        # this message unblocks the Redis listen command
        pubsub.subscribe('MODULATETONE_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    chanval = float(item['data'])
                    with lock:
                        chanval = EEGsynth.rescale(chanval, slope=scale_control, offset=offset_control)
                        chanval = EEGsynth.limit(chanval, lo=0, hi=1)
                        control[self.tone, self.audiochannel] = chanval
                    monitor.update(channame[self.audiochannel] + " tone" + str(self.tone + 1), chanval)


def callback(in_data, frame_count, time_info, status):
    global rate, nchans, ntones, control, frequencies, lock, offset

    dat = np.zeros([frame_count, nchans], dtype=np.float32)

    offset += frame_count / rate
    time = np.arange(0, frame_count) / rate + offset

    with lock:
        for chan in range(0, nchans):
            # only compute the sine for tones with a non-zero amplitude
            for tone in np.nonzero(control[:, chan])[0]:
                dat[:, chan] += control[tone, chan] * np.sin(2.0 * np.pi * frequencies[tone] * time)

    try:
        # this is for Python 2
        buf = np.getbuffer(dat)
    except:
        # this is for Python 3
        buf = dat.tobytes()

    return buf, pyaudio.paContinue


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inifile", default=os.path.join(path, name + '.ini'),
                        help="name of the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    config.read(args.inifile)

    try:
        r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint(
            'redis', 'port'), db=0, charset='utf-8', decode_responses=True)
        response = r.client_list()
    except redis.ConnectionError:
        raise RuntimeError("cannot connect to Redis server")

    # combine the patching from the configuration file and Redis
    patch = EEGsynth.patch(config, r)

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global parser, args, config, r, response, patch, monitor, debug
    global device, mode, rate, offset, control, scale_control, offset_control, nchans, channame, ntones, frequencies, lock, stream, trigger, thread, p

    # get the options from the configuration file
    device = patch.getint('audio', 'device')
    mode = patch.getstring('audio', 'mode', default='mono')
    rate = patch.getint('audio', 'rate', default=22050)
    frequencies = patch.getfloat('audio', 'frequencies', multiple=True)

    # initialize the time offset, this will be incremented by the callback
    offset = 0.

    # these are for multiplying/attenuating the control signale
    scale_control = patch.getfloat('scale', 'control', default=0.125)
    offset_control = patch.getfloat('offset', 'control', default=0)

    if mode == 'mono':
        nchans = 1
    elif mode == 'stereo':
        nchans = 2
    elif mode == 'quad':
        nchans = 4

    ntones = len(frequencies)
    control = np.zeros((ntones, nchans), dtype=np.float32)

    monitor.info("audio nchans = " + str(nchans))
    monitor.info("audio ntones = " + str(ntones))
    monitor.info("audio rate   = " + str(rate))

    # this is to prevent two triggers from being activated at the same time
    lock = threading.Lock()

    trigger = []
    # configure the trigger threads for the control signals
    channame = ['left', 'right', 'chan3', 'chan4']
    for chan in range(0, nchans):
        for tone in range(0, ntones):
            tonestr = "tone%d" % (tone + 1)
            if patch.hasitem(channame[chan], tonestr):
                redischannel = patch.getstring(channame[chan], tonestr)
                trigger.append(TriggerThread(redischannel, chan, tone))
                monitor.info("configured " + channame[chan] + " " + tonestr + " as " + redischannel)
            else:
                monitor.info("not configured " + channame[chan] + " " + tonestr)

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    p = pyaudio.PyAudio()

    monitor.info('------------------------------------------------------------------')
    info = p.get_host_api_info_by_index(0)
    monitor.info(info)
    monitor.info('------------------------------------------------------------------')
    for i in range(info.get('deviceCount')):
        if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
            monitor.info("Input  Device id " + str(i) + " - " +
                         p.get_device_info_by_host_api_device_index(0, i).get('name'))
        if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
            monitor.info("Output Device id " + str(i) + " - " +
                         p.get_device_info_by_host_api_device_index(0, i).get('name'))
    monitor.info('------------------------------------------------------------------')
    devinfo = p.get_device_info_by_index(device)
    monitor.info("Selected device is " + devinfo['name'])
    monitor.info(devinfo)
    monitor.info('------------------------------------------------------------------')

    stream = p.open(format=pyaudio.paFloat32,
                    channels=nchans,
                    rate=rate,
                    output=True,
                    output_device_index=device,
                    stream_callback=callback)

    # start the output stream
    stream.start_stream()

    signal.signal(signal.SIGINT, _stop)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    pass


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, offset
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt
    '''
    global monitor, trigger, r, stream, p
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('MODULATETONE_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    stream.stop_stream()
    stream.close()
    p.terminate()
    sys.exit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
