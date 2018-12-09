#!/usr/bin/env python

# This module writes Redis control values and triggers to the Raspberry Pi GPIO header.
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2018, Robert Oostenveld for the EEGsynth project, http://www.eegsynth.org
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

# this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import ConfigParser
import argparse
import os
import redis
import sys
import time
import threading
import wiringpi

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder, '../../lib'))
import EEGsynth
import EDF

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

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

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
delay = patch.getfloat('general', 'delay')
# control values for PWM should be between 0 and 100
input_scale = patch.getfloat('input', 'scale', default=100)
input_offset = patch.getfloat('input', 'offset', default=0)
# values between 0 and 1 are quite nice for the duration
duration_scale = patch.getfloat('duration', 'scale', default=1)
duration_offset = patch.getfloat('duration', 'offset', default=0)

# this is to prevent two triggers from being activated at the same time
lock = threading.Lock()


def SetGPIO(gpio, val=1):
    lock.acquire()
    if debug > 1:
        print gpio, pin[gpio], val
    wiringpi.digitalWrite(pin[gpio], val)
    lock.release()


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
                    # switch to the PWM value specified in the event
                    val = item['data']
                    val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
                    val = int(val)
                    SetGPIO(self.gpio, val)
                    if self.duration != None:
                        # schedule a timer to switch it off after the specified duration
                        duration = patch.getfloat('duration', self.gpio)
                        duration = EEGsynth.rescale(duration, slope=duration_scale, offset=duration_offset)
                        # some minimal time is needed for the delay
                        duration = EEGsynth.limit(duration, 0.05, float('Inf'))
                        t = threading.Timer(duration, SetGPIO, args=[self.gpio, 0])
                        t.start()


# use the WiringPi numbering, see http://wiringpi.com/reference/setup/
wiringpi.wiringPiSetup()

# set up PWM for the control channels
previous_val = {}
for gpio, channel in config.items('control'):
    print "control", channel, gpio
    wiringpi.softPwmCreate(pin[gpio], 0, 100)
    # control values are only relevant when different from the previous value
    previous_val[gpio] = None

# create the threads that deal with the triggers
trigger = []
for gpio, channel in config.items('trigger'):
    wiringpi.pinMode(pin[gpio], 1)
    try:
        duration = patch.getstring('duration', gpio)
    except:
        duration = None
    trigger.append(TriggerThread(channel, gpio, duration))
    print "trigger", channel, gpio

# start the thread for each of the triggers
for thread in trigger:
    thread.start()


try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        for gpio, channel in config.items('control'):
            val = patch.getfloat('control', gpio)
            if val == None:
                continue  # it should be skipped when not present
            if val == previous_val[gpio]:
                continue  # it should be skipped when identical to the previous value
            previous_val[gpio] = val
            val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
            val = EEGsynth.limit(val, 0, 100)
            val = int(val)
            lock.acquire()
            wiringpi.softPwmWrite(pin[gpio], val)
            lock.release()

except KeyboardInterrupt:
    print "Closing threads"
    for thread in trigger:
        thread.stop()
    r.publish('OUTPUTGPIO_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
