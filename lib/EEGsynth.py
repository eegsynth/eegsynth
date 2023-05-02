# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2023 EEGsynth project
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

from __future__ import print_function

import os
import sys

# exclude some eegsynth/module directories from the path
for i, dir in enumerate(sys.path):
    if dir.endswith(os.path.join('module', 'redis')):
        del sys.path[i]
        continue
    if dir.endswith(os.path.join('module', 'logging')):
        del sys.path[i]
        continue

import configparser
import argparse
import time
import threading
import math
import numpy as np
from scipy.signal import firwin, butter, bessel, lfilter, lfiltic, iirnotch
import logging
from logging import Formatter
import colorama
import random
import redis          # this is NOT eegsynth/module/redis
import ZmqRedis       # this offers an alternative to a real redis server
import FakeRedis      # this offers an alternative to a real redis server
import DummyRedis     # this offers an alternative to a real redis server
import string
import termcolor
import platform
import ctypes
from termcolor import colored

###################################################################################################
class patch():
    """Class to provide a generalized interface for patching modules using
    command-line arguments, configuration files and Redis.

    The patch is initialized like this
      patch = EEGsynth.patch(name=<name>, path=<path>)
    where the name and path point to the ini file. You can also
    pass the --inifile option on the command-line.

    The following method sets and publishes the value to Redis
      patch.setvalue(key, value)

    The following method gets the value (as a string) from the command-line
    arguments or from the ini file
      patch.get(section, item, default=None)

    The following methods get the values either from the command-line
    arguments, from the ini file or from Redis
      patch.getfloat(section, item, multiple=False, default=None)
      patch.getint(section, item, multiple=False, default=None)
      patch.getstring(section, item, multiple=False, default=None)

    The formatting of options on the command-line should be like this
      --section-item value

    The formatting of options in the ini file should be like this
      [section]
      item=1            this returns 1
      item=key          get the value of the key from Redis
    or to return multiple items the formatting should be like this
      [section]
      item=1-20         this returns [1,20]
      item=1,2,3        this returns [1,2,3]
      item=1,2,3,5-9    this returns [1,2,3,5,9], not [1,2,3,5,6,7,8,9]
      item=key1,key2    get the value of key1 and key2 from Redis
      item=key1,5       get the value of key1 from Redis
      item=0,key2       get the value of key2 from Redis
    """

    def __init__(self, name=None, path=None, preservecase=False):

        if not name==None and not path==None:
            inifile = os.path.join(path, name + '.ini')
        elif not name==None:
            inifile = name + '.ini'
        else:
            inifile = None

        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--inifile", default=inifile, help="name of the configuration file")
        parser.add_argument("--general-broker", default=None, help="general broker")
        parser.add_argument("--general-debug", default=None, help="general debug")
        parser.add_argument("--general-delay", default=None, help="general delay")
        parser.add_argument("--general-logging", default=None, help="general logging")
        args = parser.parse_args()

        config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        if preservecase:
            # see https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
            config.optionxform = str
        if 'inifile' in args and not args.inifile==None:
            config.read(args.inifile)

        # convert the command-line arguments in a dict
        args = vars(args)
        # remove empty items
        args = {k:v for k,v in args.items() if v}

        if 'general_broker' in args:
            broker = args['general_broker']
        elif config.has_option('general', 'broker'):
            broker = config.get('general', 'broker')
        else:
            # set the default broker
            if config.has_section('redis'):
                broker = 'redis'
            elif config.has_section('zeromq'):
                broker = 'zeromq'
            else:
                broker = 'dummy'

        if broker=='redis':
            if config.has_option('redis', 'hostname'):
                hostname = config.get('redis', 'hostname')
            else:
                hostname = 'localhost'
            if config.has_option('redis', 'port'):
                port = config.getint('redis', 'port')
            else:
                port = 6379
            try:
                r = redis.StrictRedis(host=hostname, port=port, db=0, charset='utf-8', decode_responses=True)
                response = r.client_list()
            except redis.ConnectionError:
                raise RuntimeError("cannot connect to Redis server")

        elif broker=='zeromq':
            # make a connection to the specified ZeroMQ server
            # the combination of server and client emulate a subset of redis functionality
            if config.has_option('zeromq', 'hostname'):
                hostname = config.get('zeromq', 'hostname')
            else:
                hostname = 'localhost'
            if config.has_option('zeromq', 'port'):
                port = config.getint('zeromq', 'port')
            else:
                port = 5555
            if config.has_option('zeromq', 'timeout'):
                timeout = config.getint('zeromq', 'timeout')
            else:
                timeout = 5000
            r = ZmqRedis.client(host=hostname, port=port, timeout=timeout)
            if not name=='redis' and not r.connect():
                raise RuntimeError("cannot connect to ZeroMQ server")

        elif broker=='fake':
            # the fake client stores all values in a dictionary
            r = DummyRedis.client()

        elif broker=='dummy':
            # the dummy client has all functions but does not do anything
            r = DummyRedis.client()

        else:
            raise RuntimeError("unknown broker")

        # store the command-line arguments, the configuration object that maps the ini file, and the Redis connection
        self.args = args
        self.config = config
        self.redis = r              # this can be redis, zeromq, fake or dummy

    ####################################################################
    def pubsub(self):
        return self.redis.pubsub()

    ####################################################################
    def publish(self, channel, value):
        return self.redis.publish(channel, value)

    ####################################################################
    def get(self, section, item, default=None):
        if section + "_" + item in self.args:
            return self.args[section + "_" + item]
        elif self.config.has_option(section, item):
            return self.config.get(section, item)
        else:
            return default

    ####################################################################
    def getfloat(self, section, item, multiple=False, default=None):
        if section + "_" + item in self.args:
            # get it from the command-line arguments
            return float(self.args[section + "_" + item])
        elif self.config.has_option(section, item) and len(self.config.get(section, item))>0:
            # get all items from the ini file, there might be one or multiple
            items = self.config.get(section, item)

            if multiple:
                # convert the items to a list
                if items.find(",") > -1:
                    separator = ","
                elif items.find("-") > -1:
                    separator = "-"
                elif items.find("\t") > -1:
                    separator = "\t"
                else:
                    separator = " "
                items = squeeze(' ', items)        # remove excess whitespace
                items = squeeze(separator, items)  # remove double separators
                items = items.split(separator)     # split on the separator
            else:
                # make a list with a single item
                items = [items]

            # set the default
            if multiple and isinstance(default, list):
                val = [float(x) for x in default]
            elif default != None:
                val = [float(default)] * len(items)
            else:
                val = [default] * len(items)

            # convert the strings into floating point values
            for i,item in enumerate(items):
                try:
                    # if it resembles a value, use that
                    val[i] = float(item)
                except ValueError:
                    # if it is a string, get the value from Redis
                    try:
                        val[i] = float(self.redis.get(item))
                    except TypeError:
                        pass
        else:
            # the configuration file does not contain the item
            if multiple and isinstance(default, list):
                val = [float(x) for x in default]
            elif multiple and default == None:
                val = []
            elif multiple and default != None:
                val = [float(default)]
            elif not multiple and default == None:
                val = default
            elif not multiple and default != None:
                val = float(default)

        if multiple and not isinstance(val, list):
            # return a list
            return [val]
        elif not multiple and isinstance(val, list):
            # return a single value
            return val[0]
        else:
            return val

    ####################################################################
    def getint(self, section, item, multiple=False, default=None):
        if section + "_" + item in self.args:
            return int(self.args[section + "_" + item])
        elif self.config.has_option(section, item) and len(self.config.get(section, item))>0:
            # get all items from the ini file, there might be one or multiple
            items = self.config.get(section, item)

            if multiple:
                # convert the items to a list
                if items.find(",") > -1:
                    separator = ","
                elif items.find("-") > -1:
                    separator = "-"
                elif items.find("\t") > -1:
                    separator = "\t"
                else:
                    separator = " "
                items = squeeze(' ', items)        # remove excess whitespace
                items = squeeze(separator, items)  # remove double separators
                items = items.split(separator)     # split on the separator
            else:
                # make a list with a single item
                items = [items]

            # set the default
            if multiple and isinstance(default, list):
                val = [int(x) for x in default]
            elif default != None:
                val = [int(default)] * len(items)
            else:
                val = [default] * len(items)

            # convert the strings into integer values
            for i,item in enumerate(items):
                try:
                    # if it resembles a value, use that
                    val[i] = int(item)
                except ValueError:
                    # if it is a string, get the value from Redis
                    try:
                        val[i] = int(round(float(self.redis.get(item))))
                    except TypeError:
                        pass
        else:
            # the configuration file does not contain the item
            if multiple and isinstance(default, list):
                val = [int(x) for x in default]
            elif multiple and default == None:
                val = []
            elif multiple and default != None:
                val = [int(default)]
            elif not multiple and default == None:
                val = default
            elif not multiple and default != None:
                val = int(default)

        if multiple and not isinstance(val, list):
            # return a list
            return [val]
        elif not multiple and isinstance(val, list):
            # return a single value
            return val[0]
        else:
            return val

    ####################################################################
    def getstring(self, section, item, multiple=False, default=None):
        if section + "_" + item in self.args:
            return self.args[section + "_" + item]
        else:
            # get all items from the ini file, there might be one or multiple
            try:
                val = self.config.get(section, item)
                if self.redis.exists(val):
                    # the ini file points to a Redis key, which contains the actual value
                    val = self.redis.get(val)
            except:
                val = default

        if multiple:
            if val==None or len(val)==0:
                # convert it to an empty list
                val = []
            else:
                # convert the string with items to a list
                if val.find(",") > -1:
                    separator = ","
                elif val.find("-") > -1:
                    separator = "-"
                elif val.find("\t") > -1:
                    separator = "\t"
                else:
                    separator = " "

                val = squeeze(separator, val)  # remove double separators
                val = val.split(separator)     # split on the separator

        if multiple and not isinstance(val, list):
            # return a list
            return [val]
        elif not multiple and isinstance(val, list):
            # return a single value
            return val[0]
        else:
            return val

    ####################################################################
    def hasitem(self, section, item):
        # check whether an item is present on the command line or in the ini file
        if section + "_" + item in self.args:
            return True
        else:
            return self.config.has_option(section, item)

    ####################################################################
    def setvalue(self, item, val, duration=0):
        self.redis.set(item, val)      # set it as control channel
        self.redis.publish(item, val)  # send it as trigger
        if duration > 0:
            # switch off after a certain amount of time
            threading.Timer(duration, self.setvalue, args=[item, 0.]).start()

###################################################################################################
class monitor():
    """Class to monitor control values and print them to screen when they have changed. It also
    prints a boilerplate license upon startup.

    monitor.loop()           - to be called on every iteration of the loop
    monitor.update(key, val) - to be used to check whether values change

    monitor.critical(...)  - shows always
    monitor.error(...)     - shows always
    monitor.warning(...)   - shows always
    monitor.success(...)   - debug level 0
    monitor.info(...)      - debug level 1
    monitor.debug(...)     - debug level 2
    monitor.trace(...)     - debug level 3
    """

    def __init__(self, name=None, debug=0, patch=None, target=None):
        self.previous_value = {}
        self.loop_time = None
        self.patch = patch
        self.target = target

        # on Windows this will cause anything with ANSI color codes sent to stdout or stderr converted to the Windows versions
        colorama.init()

        logger = logging.getLogger(name)

        if target and patch:
            redisHandler = RedisLogger(self.patch.redis, target)
            redisHandler.setFormatter(logging.Formatter('%(levelname)s: %(name)s: %(message)s'))
            # '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logger.addHandler(redisHandler)
        else:
            streamHandler = logging.StreamHandler()
            streamHandler.setFormatter(ColoredFormatter(name))
            logger.addHandler(streamHandler)

        # add a success level
        logging.SUCCESS = logging.INFO + 5
        logging.addLevelName(logging.SUCCESS, 'SUCCESS')

        # add a trace level
        logging.TRACE = logging.DEBUG - 5
        logging.addLevelName(logging.TRACE, 'TRACE')

        if debug==0:
            logger.setLevel(logging.SUCCESS)
        elif debug==1:
            logger.setLevel(logging.INFO)
        elif debug==2:
            logger.setLevel(logging.DEBUG)
        elif debug==3:
            logger.setLevel(logging.TRACE)

        # remember the logger
        self.logger = logger

        if name == None:
            fullname = 'This software'
        else:
            fullname = 'The %s module' % (name)

        print("""
##############################################################################
# %s is part of EEGsynth, see <http://www.eegsynth.org>.
#
# Copyright (C) 2017-2023 EEGsynth project
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
##############################################################################

Press Ctrl-C to stop this module.
        """ % (fullname))

    def setTarget(self, target):
        self.target = target

    def setPatch(self, patch):
        self.patch = patch

    def setLevel(self, level):
        if level==0:
            self.logger.setLevel(logging.SUCCESS)
        elif level==1:
            self.logger.setLevel(logging.INFO)
        elif level==2:
            self.logger.setLevel(logging.DEBUG)
        elif level==3:
            self.logger.setLevel(logging.TRACE)

    def loop(self, feedback=1.0, duration=None):
        now = time.time()

        if self.loop_time is None:
            self.success("starting loop...")
            self.loop_time = now
            self.loop_count = 0
            self.loop_start = time.time()
        else:
            self.loop_count += 1
        elapsed = now - self.loop_time
        if feedback and elapsed>=feedback:
            self.info("looping with %d iterations in %g seconds" % (self.loop_count, elapsed))
            self.loop_time = now
            self.loop_count = 0
        if duration!=None and now-self.loop_start>duration:
            raise SystemExit

    def update(self, key, val, level='info'):
        if (key not in self.previous_value) or (self.previous_value[key]!=val):
            try:
                # the comparison returns false in case both are nan
                a = math.isnan(self.previous_value[key])
                b = math.isnan(val)
                if (a and b):
                    return False
            except:
                pass

            if level == 'critical':
                self.critical(formatkeyval(key, val))
            elif level == 'error':
                self.error(formatkeyval(key, val))
            elif level == 'warning':
                self.warning(formatkeyval(key, val))
            elif level == 'success':
                self.success(formatkeyval(key, val))
            elif level == 'info':
                self.info(formatkeyval(key, val))
            elif level == 'debug':
                self.debug(formatkeyval(key, val))
            elif level == 'trace':
                self.trace(formatkeyval(key, val))

            self.previous_value[key] = val
            return True
        else:
            return False

    def critical(self, *args):
        if len(args)==1:
            self.logger.log(logging.CRITICAL, *args)
        else:
            self.logger.log(logging.CRITICAL, " ".join(map(format, args)))

    def error(self, *args):
        if len(args)==1:
            self.logger.log(logging.ERROR, *args)
        else:
            self.logger.log(logging.ERROR, " ".join(map(format, args)))

    def warning(self, *args):
        if len(args)==1:
            self.logger.log(logging.WARNING, *args)
        else:
            self.logger.log(logging.WARNING, " ".join(map(format, args)))

    def success(self, *args):
        if len(args)==1:
            self.logger.log(logging.SUCCESS, *args)
        else:
            self.logger.log(logging.SUCCESS, " ".join(map(format, args)))

    def info(self, *args):
        if len(args)==1:
            self.logger.log(logging.INFO, *args)
        else:
            self.logger.log(logging.INFO, " ".join(map(format, args)))

    def debug(self, *args):
        if len(args)==1:
            self.logger.log(logging.DEBUG, *args)
        else:
            self.logger.log(logging.DEBUG, " ".join(map(format, args)))

    def trace(self, *args):
        if len(args)==1:
            self.logger.log(logging.TRACE, *args)
        else:
            self.logger.log(logging.TRACE, " ".join(map(format, args)))


###################################################################################################
class RedisLogger(logging.Handler):
    """Class to send logging messages to Redis
    """

    def __init__(self, server, channel):
        super().__init__()
        self.redis = server
        self.channel = channel

    def emit(self, record):
        msg = self.format(record)
        self.redis.set(self.channel, msg)
        self.redis.publish(self.channel, msg)

###################################################################################################
class ColoredFormatter(Formatter):
    """Class to format logging messages
    """

    def __init__(self, name=None):
        self.name = name
        colors = list(termcolor.COLORS.keys()) # prevent RuntimeError: dictionary changed size during iteration
        # add reverse and bright color
        for color in colors:
            termcolor.COLORS['reverse_'+color] = termcolor.COLORS[color]+10
            termcolor.COLORS['bright_'+color] = termcolor.COLORS[color]+60
        # for color in termcolor.COLORS.keys():
        #     print(colored(color, color))

    def format(self, record):
        colors = {
            'CRITICAL': 'reverse_red',
            'ERROR': 'red',
            'WARNING': 'yellow',
            'SUCCESS': 'green',
            'INFO': 'cyan',
            'DEBUG': 'bright_grey',
            'TRACE': 'reverse_white',
        }
        color = colors.get(record.levelname, 'white')
        if self.name:
            return colored(record.levelname, color) + ': ' + self.name + ': ' + record.getMessage()
        else:
            return colored(record.levelname, color) + ': ' + record.getMessage()

####################################################################
def rescale(xval, slope=None, offset=None, reverse=False):
    if hasattr(xval, "__iter__"):
        return [rescale(x, slope, offset) for x in xval]
    elif xval == None:
        return None
    else:
        if slope==None:
            slope = 1.0
        if offset==None:
            offset = 0.0
        if reverse:
            return (float(xval) - float(offset))/float(slope)
        else:
            return float(slope)*float(xval) + float(offset)

####################################################################
def limit(xval, lo=0.0, hi=127.0):
    if hasattr(xval, "__iter__"):
        return [limit(x, lo, hi) for x in xval]
    elif xval == None:
        return None
    else:
        xval = float(xval)
        lo = float(lo)
        hi = float(hi)
        if xval < lo:
            return lo
        elif xval > hi:
            return hi
        else:
            return xval

####################################################################
def compress(xval, lo=0.5, hi=0.5, range=1.0):
    if hasattr(xval, "__iter__"):
        return [compress(x, lo, hi, range) for x in xval]
    else:
        xval  = float(xval)
        lo    = float(lo)
        hi    = float(hi)
        range = float(range)

        if lo>range/2:
          ax = 0.0
          ay = lo-range/2
        else:
          ax = range/2-lo
          ay = 0.0

        if hi<range/2:
          bx = range
          by = range/2+hi
        else:
          bx = 1.5*range-hi
          by = range

        if (bx-ax)==0:
            # threshold the value halfway
            yval = (xval>0.5)*range
        else:
            # map the value according to a linear transformation
            slope     = (by-ay)/(bx-ax)
            intercept = ay - ax*slope
            yval      = (slope*xval + intercept)

        if yval<0:
          yval = 0
        elif yval>range:
          yval = range

        return yval

####################################################################
def normalizerange(xval, min, max):
    min = float(min)
    max = float(max)
    return (float(xval)-min)/(max-min)

####################################################################
def normalizestandard(xval, avg, std):
    avg = float(avg)
    std = float(std)
    return (float(xval)-avg)/std

####################################################################
def squeeze(char, string):
    while char*2 in string:
        string = string.replace(char*2, char)
    return string

####################################################################
def initialize_online_notchfilter(fsample, fnotch, quality, x, axis=-1):
    nyquist = fsample / 2.
    ndim = len(x.shape)
    axis = axis % ndim

    if fnotch != None:
        fnotch = fnotch/nyquist
        if fnotch < 0.001:
            fnotch = None
        elif fnotch > 0.999:
            fnotch = None

    if not(fnotch == None) and (quality>0):
        print('using NOTCH filter', [fnotch, quality])
        b, a = iirnotch(fnotch, quality)
    else:
        # no filtering at all
        print('using IDENTITY filter', [fnotch, quality])
        b = np.ones(1)
        a = np.ones(1)

    # initialize the state for the filtering based on the previous data
    if ndim == 1:
        zi = zi = lfiltic(b, a, x, x)
    elif ndim == 2:
        f = lambda x : lfiltic(b, a, x, x)
        zi = np.apply_along_axis(f, axis, x)

    return b, a, zi

####################################################################
def initialize_online_filter(fsample, highpass, lowpass, order, x, axis=-1):
    # boxcar, triang, blackman, hamming, hann, bartlett, flattop, parzen, bohman, blackmanharris, nuttall, barthann
    filtwin = 'nuttall'
    nyquist = fsample / 2.
    ndim = len(x.shape)
    axis = axis % ndim

    if highpass != None:
        highpass = highpass/nyquist
        if highpass < 0.001:
            print('Warning: highpass is too low, disabling')
            highpass = None
        elif highpass > 0.999:
            print('Warning: highpass is too high, disabling')
            highpass = None

    if lowpass != None:
        lowpass = lowpass/nyquist
        if lowpass < 0.001:
            print('Warning: lowpass is too low, disabling')
            lowpass = None
        elif lowpass > 0.999:
            print('Warning: lowpass is too low, disabling')
            lowpass = None

    if not(highpass is None) and not(lowpass is None) and highpass>=lowpass:
        # totally blocking all signal
        print('using NULL filter', [highpass, lowpass, order])
        b = np.zeros(order)
        a = np.ones(1)
    elif not(lowpass is None) and (highpass is None):
        print('using lowpass filter', [highpass, lowpass, order])
        b = firwin(order, cutoff = lowpass, window = filtwin, pass_zero = True)
        a = np.ones(1)
    elif not(highpass is None) and (lowpass is None):
        print('using highpass filter', [highpass, lowpass, order])
        b = firwin(order, cutoff = highpass, window = filtwin, pass_zero = False)
        a = np.ones(1)
    elif not(highpass is None) and not(lowpass is None):
        print('using bandpass filter', [highpass, lowpass, order])
        b = firwin(order, cutoff = [highpass, lowpass], window = filtwin,
                    pass_zero = False)
        a = np.ones(1)
    else:
        # no filtering at all
        print('using IDENTITY filter', [highpass, lowpass, order])
        b = np.ones(1)
        a = np.ones(1)

    # initialize the state for the filtering based on the previous data
    if ndim == 1:
        zi = zi = lfiltic(b, a, x, x)
    elif ndim == 2:
        f = lambda x : lfiltic(b, a, x, x)
        zi = np.apply_along_axis(f, axis, x)

    return b, a, zi

####################################################################
def online_filter(b, a, x, axis=-1, zi=[]):
    y, zo = lfilter(b, a, x, axis=axis, zi=zi)
    return y, zo

####################################################################
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

####################################################################
def bessel_bandpass(lowcut, highcut, fs, order):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = bessel(order, [low, high], btype="bandpass", output="sos")
    return sos

####################################################################
def butter_lowpass(lowcut, fs, order=9):
    nyq = 0.5 * fs
    low = lowcut / nyq
    b, a = butter(order, low, btype='lowpass')
    return b, a

####################################################################
def butter_highpass(highcut, fs, order=9):
    nyq = 0.5 * fs
    high = highcut / nyq
    b, a = butter(order, high, btype='highpass')
    return b, a

####################################################################
def bessel_highpass(cutoff, fs, order):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    sos = bessel(order, normal_cutoff, btype="highpass", output="sos")
    return sos

####################################################################
def notch(f0, fs, Q=5):
    # Q = Quality factor
    nyq = 0.5 * fs
    w0 = f0 / nyq
    b, a = iirnotch(w0, Q)
    return b, a

####################################################################
def butter_bandpass_filter(dat, lowcut, highcut, fs, order=5):
    '''
    This filter does not retain state and is not optimal for online filtering.
    '''
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, dat)
    return y

####################################################################
def butter_lowpass_filter(dat, lowcut, fs, order=9):
    '''
    This filter does not retain state and is not optimal for online filtering.
    '''
    b, a = butter_lowpass(lowcut, fs, order=order)
    y = lfilter(b, a, dat)
    return y

####################################################################
def butter_highpass_filter(dat, highcut, fs, order=9):
    '''
    This filter does not retain state and is not optimal for online filtering.
    '''
    b, a = butter_highpass(highcut, fs, order=order)
    y = lfilter(b, a, dat)
    return y

####################################################################
def notch_filter(dat, f0, fs, Q=30, dir='onepass'):
    '''
    This filter does not retain state and is not optimal for online filtering.
    The fiter direction can be specified as
        'onepass'         forward filter only
        'onepass-reverse' reverse filter only, i.e. backward in time
        'twopass'         zero-phase forward and reverse filter
        'twopass-reverse' zero-phase reverse and forward filter
        'twopass-average' average of the twopass and the twopass-reverse
    '''

    b, a = notch(f0, fs, Q=Q)
    if dir=='onepass':
        y = lfilter(b, a, dat)
    elif dir=='onepass-reverse':
        y = dat
        y = np.flip(y, 1)
        y = lfilter(b, a, y)
        y = np.flip(y, 1)
    elif dir=='twopass':
        y = dat
        y = lfilter(b, a, y)
        y = np.flip(y, 1)
        y = lfilter(b, a, y)
        y = np.flip(y, 1)
    elif dir=='twopass-reverse':
        y = dat
        y = np.flip(y, 1)
        y = lfilter(b, a, y)
        y = np.flip(y, 1)
        y = lfilter(b, a, y)
    elif dir=='twopass-average':
        # forward
        y1 = dat
        y1 = lfilter(b, a, y1)
        y1 = np.flip(y1, 1)
        y1 = lfilter(b, a, y1)
        y1 = np.flip(y1, 1)
        # reverse
        y2 = dat
        y2 = np.flip(y2, 1)
        y2 = lfilter(b, a, y2)
        y2 = np.flip(y2, 1)
        y2 = lfilter(b, a, y2)
        # average
        y = (y1 + y2)/2
    return y

###################################################################################################
def formatkeyval(key, val):
    if sys.version_info < (3,0):
        # this works in Python 2, but fails in Python 3
        isstring = isinstance(val, basestring)
    else:
        # this works in Python 3, but fails for unicode strings in Python 2
        isstring = isinstance(val, str)
    if val is None:
        output = "%s = None" % (key)
    elif isinstance(val, list):
        output = "%s = %s" % (key, str(val))
    elif isstring:
        output = "%s = %s" % (key, val)
    else:
        output = "%s = %g" % (key, val)
    return output

###################################################################################################
def trimquotes(option):
    # remove leading and trailing quotation marks
    # this is needed to include leading or trailing spaces in an ini-file option
    if option[0]=='"':
        option = option[1:]
    if option[0]=='\'':
        option = option[1:]
    if option[-1]=='"':
        option = option[0:-1]
    if option[-1]=='\'':
        option = option[0:-1]
    return option

###################################################################################################
def uuid(length):
    return ''.join(random.choice(string.hexdigits) for i in range(length))

###################################################################################################
def appid(myappid):
    # the icon in the taskbar should not be the python interpreter but the EEGsynth logo
    if platform.system() == 'Windows':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
