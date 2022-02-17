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
        global modulation, frequencies, control, channame, scale_amplitude, offset_amplitude, scale_frequency, offset_frequency
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
                        if modulation == 'am':
                            chanval = EEGsynth.rescale(chanval, slope=scale_amplitude, offset=offset_amplitude)
                            chanval = EEGsynth.limit(chanval, lo=0, hi=1)
                        elif modulation == 'fm':
                            chanval = EEGsynth.rescale(chanval, slope=scale_frequency, offset=offset_frequency)
                        control[self.tone, self.audiochannel] = chanval
                    monitor.update(channame[self.audiochannel] + " tone" + str(self.tone + 1), chanval)


def callback(in_data, blocksize, time_info, status):
    global rate, modulation, nchans, ntones, control, frequencies, scale_amplitude, lock, offset

    dat = np.zeros([blocksize, nchans], dtype=np.float32)
    timeaxis = np.arange(0, blocksize) / rate

    if modulation == 'am':
        # apply and remember the time offset, this is the same for each note
        timeaxis += offset
        offset += blocksize / rate
    elif modulation == 'fm':
        # the phase offset is different for each note and therefore handled below
        pass

    with lock:
        for chan in range(0, nchans):
            if modulation == 'am':
                # only compute tones with a non-zero amplitude
                for tone in np.nonzero(control[:, chan])[0]:
                    phase = 2.0 * np.pi * frequencies[tone] * timeaxis
                    dat[:, chan] += control[tone, chan] * np.sin(phase)
            elif modulation == 'fm':
                # all tones will contribute and need to be computed
                for tone in range(0, ntones):
                    phase = 2.0 * np.pi * (frequencies[tone] + control[tone, chan]) * timeaxis + offset[tone, chan]
                    offset[tone, chan] = phase[-1]
                    dat[:, chan] += scale_amplitude * np.sin(phase)

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
    global device, mode, rate, modulation, offset, control, scale_amplitude, offset_amplitude, scale_frequency, offset_frequency, nchans, channame, ntones, frequencies, lock, stream, trigger, thread, p

    # get the options from the configuration file
    device = patch.getint('audio', 'device')
    rate = patch.getint('audio', 'rate', default=22050)
    nchans = patch.getint("audio", "nchans", default=2)
    modulation = patch.getstring('audio', 'modulation', default='am')
    frequencies = patch.getfloat('audio', 'frequencies', multiple=True)

    # these are for multiplying/attenuating the amplitude
    scale_amplitude = patch.getfloat('scale', 'amplitude', default=0.125)   # the default is for 8 controls
    offset_amplitude = patch.getfloat('offset', 'amplitude', default=0)
    scale_frequency = patch.getfloat('scale', 'frequency', default=100)     # the default is 100 Hz
    offset_frequency = patch.getfloat('offset', 'frequency', default=0)

    ntones = len(frequencies)
    control = np.zeros((ntones, nchans), dtype=np.float32)

    # initialize the time/phase offset, this will be incremented by the callback
    if modulation == 'am':
        offset = 0.
    elif modulation == 'fm':
        offset = np.zeros((ntones, nchans), dtype=np.float32)

    monitor.info("audio nchans = " + str(nchans))
    monitor.info("audio ntones = " + str(ntones))
    monitor.info("audio rate   = " + str(rate))
    monitor.info("modulation   = " + modulation)

    # this is to prevent two triggers from being activated at the same time
    lock = threading.Lock()

    trigger = []
    # configure the trigger threads for the control signals
    channame = ['left', 'right', 'chan3', 'chan4', 'chan5', 'chan6', 'chan7', 'chan8']
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

    if scale_amplitude>1/ntones:
        monitor.warning('the amplitude scaling is too high, clipping might occur')

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
