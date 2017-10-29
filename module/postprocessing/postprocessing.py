#!/usr/bin/env python

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
from EEGsynth import compress, limit, rescale

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read(args.inifile)

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

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
    time.sleep(config.getfloat('general', 'delay'))

    actual_value = [];
    for name in input_name:
        actual_value.append(EEGsynth.getfloat('input', name, config, r))

    for key,equation in zip(output_name, output_equation):
        for name,value in zip(input_name, actual_value):
            if value is None and equation.count(name)>0:
                # there are undefined variables in this equation
                break
            else:
                equation = equation.replace(name, str(value))
        else:
            # this section should not run if there are undefined variables in an equation
            val = eval(equation)
            if debug>1:
                print key, '=', equation, '=', val
            r.set(key, val)             # send it as control value
