#!/usr/bin/env python

# Processtrigger performs basic algorithms upon receiving a trigger
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std, mod
from numpy import random
import configparser
import argparse
import numpy as np
import os
import redis
import sys
import time
import threading

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

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale, normalizerange, normalizestandard

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

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug'))

# get the options from the configuration file
prefix = patch.getstring('output', 'prefix')

def rand(x):
    # the input variable is ignored
    return np.asscalar(random.rand(1))

def randn(x):
    # the input variable is ignored
    return np.asscalar(random.randn(1))

def sanitize(equation):
    equation.replace(' ', '')
    equation = equation.replace('(', '( ')
    equation = equation.replace(')', ' )')
    equation = equation.replace('+', ' + ')
    equation = equation.replace('-', ' - ')
    equation = equation.replace('*', ' * ')
    equation = equation.replace('/', ' / ')
    equation = equation.replace(',', ' , ')
    equation = equation.replace('>', ' > ')
    equation = equation.replace('<', ' < ')
    equation = ' '.join(equation.split())
    return equation

# assign the initial values
for item in config.items('initial'):
    val = patch.getfloat('initial', item[0])
    patch.setvalue(item[0], val)
    monitor.update(item[0], val)

# get the input variables
if len(config.items('input')):
    input_name, input_variable = list(zip(*config.items('input')))
else:
    input_name, input_variable = ([], [])

# get the output equations for each trigger
output_name = {}
output_equation = {}
for item in config.items('trigger'):
    output_name[item[0]], output_equation[item[0]] = list(zip(*config.items(item[0])))
    # make the equations robust against sub-string replacements
    output_equation[item[0]] = [sanitize(equation) for equation in output_equation[item[0]]]

monitor.info('===== input variables =====')
for name,variable in zip(input_name, input_variable):
    monitor.info(name + ' = ' + variable)
for item in config.items('trigger'):
    monitor.info('===== output equations for %s =====' % item[0])
    for name,equation in zip(output_name[item[0]], output_equation[item[0]]):
        monitor.info(name + ' = ' + equation)
monitor.info('============================')

# this is to prevent two triggers from being processed at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, trigger, redischannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.trigger = trigger
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('PROCESSTRIGGER_UNBLOCK') # this message unblocks the Redis listen command
        pubsub.subscribe(self.redischannel)        # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                        with lock:
                            monitor.debug('----- %s ----- ' % (self.redischannel))
                            input_value = []
                            for name in input_name:
                                # get the values of the input variables
                                val = patch.getfloat('input', name)
                                monitor.update(name, val)
                                input_value.append(val)

                            if patch.getint('conditional', self.trigger, default=1)==0:
                                continue

                            for key, equation in zip(output_name[self.trigger], output_equation[self.trigger]):

                                # replace the variable names in the equation by the values
                                for name, value in zip(input_name, input_value):
                                    if value is None and equation.count(name)>0:
                                        monitor.error('Undefined value: %s' % (name))
                                    else:
                                        equation = equation.replace(name, str(value))

                                # also replace the variable name for the trigger by its value
                                name  = self.trigger
                                value = float(item['data'])
                                if value is None and equation.count(name)>0:
                                    monitor.error('Undefined value: %s' % (name))
                                else:
                                    equation = equation.replace(name, str(value))

                                # try to evaluate each equation
                                try:
                                    val = eval(equation)
                                    val = float(val) # deal with True/False
                                    monitor.debug('%s = %s = %g' % (key, equation, val))
                                    patch.setvalue(key, val)
                                except ZeroDivisionError:
                                    # division by zero is not a serious error
                                    patch.setvalue(equation[0], np.NaN)
                                except:
                                    monitor.error('Error in evaluation: %s = %s' % (key, equation))

                            # send a copy of the original trigger with the given prefix
                            key = '%s.%s' % (prefix, item['channel'])
                            val = float(item['data'])
                            patch.setvalue(key, val)

# create the background threads that deal with the triggers
trigger = []
monitor.debug("Setting up threads for each trigger")
for item in config.items('trigger'):
        trigger.append(TriggerThread(item[0], item[1]))
        monitor.debug(item[0], item[1], 'OK')

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

except KeyboardInterrupt:
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('PROCESSTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
