#!/usr/bin/env python

# This module records Redis messages (i.e. triggers) to a TSV file
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
import datetime
import os
import redis
import sys
import time
import threading
import tempfile

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
monitor = EEGsynth.monitor(name=name, debug=patch.getint('general','debug'))

# get the options from the configuration file
debug        = patch.getint('general','debug')
delay        = patch.getfloat('general','delay')
input_scale  = patch.getfloat('input', 'scale', default=None)
input_offset = patch.getfloat('input', 'offset', default=None)
filename     = patch.getstring('recording', 'file')
fileformat   = 'tsv'

# start with a temporary file which is immediately closed
f            = tempfile.TemporaryFile().close()
recording    = False
filenumber   = 0

# this is to prevent two triggers from being saved at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('RECORDTRIGGER_UNBLOCK')  # this message unblocks the Redis listen command
        pubsub.subscribe(self.redischannel)        # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                timestamp = datetime.datetime.now().isoformat()
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    # the trigger value should be saved
                    if input_scale!=None or input_offset!=None:
                        try:
                            # convert it to a number and apply the scaling and the offset
                            val = float(item['data'])
                            val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
                        except ValueError:
                            # keep it as a string
                            val = item['data']
                            monitor.info(("cannot apply scaling, writing %s as string" % (self.redischannel)))
                    if not f.closed:
                        lock.acquire()
                        # write the value, it can be either a number or a string
                        f.write("%s\t%s\t%s\n" % (self.redischannel, val, timestamp))
                        lock.release()
                        monitor.info(("%s\t%s\t%s" % (self.redischannel, val, timestamp)))

# create the background threads that deal with the triggers
trigger = []
monitor.info("Setting up threads for each trigger")
for item in config.items('trigger'):
        trigger.append(TriggerThread(item[0]))
        monitor.debug(item[0], 'OK')

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general', 'delay'))

        if recording and not patch.getint('recording', 'record'):
            monitor.info("Recording disabled - closing " + fname)
            f.close()
            recording = False
            continue

        if not recording and not patch.getint('recording', 'record'):
            monitor.info("Recording is not enabled")
            time.sleep(1)

        if not recording and patch.getint('recording', 'record'):
            recording = True
            # open a new file
            name, ext = os.path.splitext(filename)
            if len(ext) == 0:
                ext = '.' + fileformat
            fname = name + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext
            monitor.info("Recording enabled - opening " + fname)
            f = open(fname, 'w')
            f.write("event\tvalue\ttimestamp\n")
            f.flush()


except KeyboardInterrupt:
    if not f.closed:
        monitor.info('Closing file')
        f.close()
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    r.publish('RECORDTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
