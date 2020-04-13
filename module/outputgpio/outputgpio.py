#!/usr/bin/env python

# This module writes Redis control values and triggers to the Raspberry Pi GPIO header.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2020 EEGsynth project
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
import threading

# The wiringpi package only works on a Raspberry Pi
# It is only used inside this specific EEGsynth module, hence it might not be installed by default
import wiringpi

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
import EDF
import EEGsynth


def SetGPIO(gpio, val=1):
    global lock, monitor
    with lock:
        wiringpi.digitalWrite(pin[gpio], val)
        monitor.debug(str(gpio) + " " + str(pin[gpio]) + " " + str(val))


class TriggerThread(threading.Thread):
    def __init__(self, redischannel, gpio, duration):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.gpio = gpio
        self.duration = duration
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        pubsub = r.pubsub()
        # this message unblocks the Redis listen command
        pubsub.subscribe('OUTPUTGPIO_UNBLOCK')
        # this message triggers the event
        pubsub.subscribe(self.redischannel)
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    # the scale and offset options are channel specific and can be changed on the fly
                    scale = patch.getfloat('scale', self.gpio, default=100)
                    offset = patch.getfloat('offset', self.gpio, default=0)
                    # switch to the PWM value specified in the event
                    val = float(item['data'])
                    val = EEGsynth.rescale(val, slope=scale, offset=offset)
                    val = int(val)
                    SetGPIO(self.gpio, val)
                    if self.duration != None:
                        # schedule a timer to switch it off after the specified duration
                        duration = patch.getfloat('duration', self.gpio)
                        duration = EEGsynth.rescale(duration, slope=scale_duration, offset=offset_duration)
                        # some minimal time is needed for the delay
                        duration = EEGsynth.limit(duration, 0.05, float('Inf'))
                        t = threading.Timer(duration, SetGPIO, args=[self.gpio, 0])
                        t.start()


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
    global monitor, pin, debug, delay, scale_duration, offset_duration, lock, trigger

    # this can be used to show parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

    # make a dictionary that maps GPIOs to the WiringPi number
    pin = {
        "gpio0": 0,
        "gpio1": 1,
        "gpio2": 2,
        "gpio3": 3,
        "gpio4": 4,
        "gpio5": 5,
        "gpio6": 6,
        "gpio7": 7,
        "gpio21": 21,
        "gpio22": 22,
        "gpio23": 23,
        "gpio24": 24,
        "gpio25": 25,
        "gpio26": 26,
        "gpio27": 27,
        "gpio28": 28,
        "gpio29": 29,
    }

    # get the options from the configuration file
    debug = patch.getint('general', 'debug')
    delay = patch.getfloat('general', 'delay')

    # values between 0 and 1 work well for the duration
    scale_duration = patch.getfloat('scale', 'duration', default=1)
    offset_duration = patch.getfloat('offset', 'duration', default=0)

    # this is to prevent two triggers from being activated at the same time
    lock = threading.Lock()

    # use the WiringPi numbering, see http://wiringpi.com/reference/setup/
    wiringpi.wiringPiSetup()

    # set up PWM for the control channels
    previous_val = {}
    for gpio, channel in config.items('control'):
        monitor.info("control " + channel + " " + gpio)
        wiringpi.softPwmCreate(pin[gpio], 0, 100)
        # control values are only relevant when different from the previous value
        previous_val[gpio] = None

    # create the threads that deal with the triggers
    trigger = []
    for gpio, channel in config.items('trigger'):
        wiringpi.pinMode(pin[gpio], 1)
        duration = patch.getstring('duration', gpio)
        trigger.append(TriggerThread(channel, gpio, duration))
        monitor.info("trigger " + channel + " " + gpio)

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global parser, args, config, r, response, patch

    for gpio, channel in config.items('control'):
        val = patch.getfloat('control', gpio)

        if val == None:
            continue  # it should be skipped when not present
        if val == previous_val[gpio]:
            continue  # it should be skipped when identical to the previous value
        previous_val[gpio] = val
        # the scale and offset options are channel specific and can be changed on the fly
        scale = patch.getfloat('scale', gpio, default=100)
        offset = patch.getfloat('offset', gpio, default=0)
        val = EEGsynth.rescale(val, slope=scale, offset=offset)
        val = EEGsynth.limit(val, 0, 100)
        val = int(val)
        with lock:
            wiringpi.softPwmWrite(pin[gpio], val)

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
    global monitor, trigger, r
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTGPIO_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
