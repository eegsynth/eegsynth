#!/usr/bin/env python

# Postprocessing performs basic algorithms on Redis data
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2022 EEGsynth project
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

from numpy import log, log2, log10, exp, power, sqrt, mean, median, var, std, mod, random
import numpy as np
import os
import sys
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global input_name, input_variable, output_name, output_equation, variable, equation

    if 'initial' in patch.config.sections():
        # assign the initial values
        for item in patch.config.items('initial'):
            val = patch.getfloat('initial', item[0], default=np.nan)
            patch.setvalue(item[0], val)
            monitor.update(item[0], val)

    # get the input and output options
    if len(patch.config.items('input')):
        input_name, input_variable = list(zip(*patch.config.items('input')))
    else:
        input_name, input_variable = ([], [])
    if len(patch.config.items('output')):
        output_name, output_equation = list(zip(*patch.config.items('output')))
    else:
        output_name, output_equation = ([], [])

    # make the equations robust against sub-string replacements
    output_equation = [sanitize(equation) for equation in output_equation]

    monitor.info('===== input variables =====')
    for name,variable in zip(input_name, input_variable):
        monitor.info(name + ' = ' + variable)
    monitor.info('===== output equations =====')
    for name,equation in zip(output_name, output_equation):
        monitor.info(name + ' = ' + equation)
    monitor.info('============================')

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global input_name, input_variable, output_name, output_equation, variable, equation

    monitor.debug('============================')

    input_value = []
    for name in input_name:
        val = patch.getfloat('input', name, default=np.nan)
        input_value.append(val)

    for key, equation in zip(output_name, output_equation):
        # replace the variable names in the equation by the values
        for name, value in zip(input_name, input_value):
            if value is None and equation.count(name)>0:
                monitor.error('Undefined value: %s' % (name))
            else:
                equation = equation.replace(name, str(value))

        # try to evaluate the equation
        try:
            equation = equation.replace('nan', 'np.nan')
            equation = equation.replace('inf', 'np.inf')
            val = eval(equation)
            val = float(val) # deal with True/False
            monitor.debug('%s = %s = %g' % (key, equation, val))
            patch.setvalue(key, val)
        except ZeroDivisionError:
            # division by zero is not a serious error
            patch.setvalue(equation[0], np.NaN)
        except:
            monitor.error('Error in evaluation: %s = %s' % (key, equation))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    pass


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
