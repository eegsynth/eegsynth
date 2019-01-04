#!/usr/bin/env python

# Postprocessing performs basic algorithms on Redis data
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2017 EEGsynth project
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import numpy as np
import os
import redis
import sys
import time

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

# these function names can be used in the equation that gets parsed
from EEGsynth import compress, limit, rescale, normalizerange, normalizestandard

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

# this determines how much debugging information gets printed
debug = patch.getint('general','debug')

# get the input and output options
input_name, input_variable = zip(*config.items('input'))
output_name, output_equation = zip(*config.items('output'))

def sanitize(equation):
    equation = equation.replace('(', '( ')
    equation = equation.replace(')', ' )')
    equation = equation.replace('+', ' + ')
    equation = equation.replace('-', ' - ')
    equation = equation.replace('*', ' * ')
    equation = equation.replace('/', ' / ')
    equation = equation.replace('  ', ' ')
    return equation

# make the equations robust against sub-string replacements
output_equation = [sanitize(equation) for equation in output_equation]

if debug>0:
    print '===== input variables ====='
    for name,variable in zip(input_name, input_variable):
        print name, '=', variable
    print '===== output equations ====='
    for name,equation in zip(output_name, output_equation):
        print name, '=', equation
    print '============================'


while True:
    time.sleep(patch.getfloat('general', 'delay'))

    actual_value = []
    for name in input_name:
        actual_value.append(patch.getfloat('input', name))

    for key,equation in zip(output_name, output_equation):
        for name,value in zip(input_name, actual_value):
            if value is None and equation.count(name)>0:
                # there are undefined variables in this equation
                break
            else:
                equation = equation.replace(name, str(value))
        else:
            # this section should not run if there are undefined variables in an equation
            try:
                val = eval(equation)
                if debug>1:
                    print key, '=', equation, '=', val
                patch.setvalue(key, val)
            except:
                print 'Error in evaluation'
