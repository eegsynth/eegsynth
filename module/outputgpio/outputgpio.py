#!/usr/bin/env python

# This module writes Rediscontrol values and triggers to the Raspberry Pi GPIO header
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import os
import redis
import sys
import time
import threading
import wiringpi

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth
import EDF

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
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
debug        = patch.getint('general','debug')
delay        = patch.getfloat('general','delay')
input_scale  = patch.getfloat('input', 'scale', default=100)
input_offset = patch.getfloat('input', 'offset', default=0)

# this is to prevent two triggers from being activated at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, gpio):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.gpio = gpio
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('OUTPUTGPIO_UNBLOCK')  # this message unblocks the Redis listen command
        pubsub.subscribe(self.redischannel)     # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                print item
                if item['channel']==self.redischannel:
                    # the trigger value should also be saved
                    val = item['data']
                    val = int(EEGsynth.rescale(val, slope=input_scale, offset=input_offset))
                    lock.acquire()
                    wiringpi.digitalWrite(pin[self.gpio], val)
                    lock.release()
                    if debug>1:
                      print self.gpio, pin[self.gpio], val

# use the WiringPi numbering, see http://wiringpi.com/reference/setup/
wiringpi.wiringPiSetup()

# set up PWM for the control channels
for gpio,channel in config.items('control'):
    wiringpi.softPwmCreate(pin[gpio], 0, 100)
    print "control", channel, gpio

# create the threads that deal with the triggers
trigger = []
for gpio,channel in config.items('trigger'):
    wiringpi.pinMode(pin[gpio], 1)
    trigger.append(TriggerThread(channel, gpio))
    print "trigger", channel, gpio

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        for gpio,channel in config.items('control'):
            val = patch.getfloat('control', gpio)
            if val==None:
                continue # it should be skipped when not present
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
