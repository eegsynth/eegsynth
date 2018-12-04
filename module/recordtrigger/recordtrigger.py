#!/usr/bin/env python

# This module records Redis messages (i.e. triggers) to a TSV file
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

import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import argparse
import datetime
import os
import redis
import sys
import time
import threading
import tempfile

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

# this determines how much debugging information gets printed
debug        = patch.getint('general','debug')
delay        = patch.getfloat('general','delay')
input_scale  = patch.getfloat('input', 'scale', default=1)
input_offset = patch.getfloat('input', 'offset', default=0)
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
                    # the trigger value should also be saved
                    val = item['data']
                    val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
                    if not f.closed:
                        lock.acquire()
                        f.write("%s\t%g\t%s\n" % (self.redischannel, val, timestamp))
                        lock.release()
                        if debug>0:
                            print("%s\t%g\t%s" % (self.redischannel, val, timestamp))

# create the background threads that deal with the triggers
trigger = []
if debug>1:
    print "Setting up threads for each trigger"
for item in config.items('trigger'):
        trigger.append(TriggerThread(item[0]))
        if debug>1:
            print item[0], 'OK'

# start the thread for each of the triggers
for thread in trigger:
    thread.start()

try:
    while True:
        time.sleep(patch.getfloat('general', 'delay'))

        if recording and not patch.getint('recording', 'record'):
            if debug>0:
                print "Recording disabled - closing", fname
            f.close()
            recording = False
            continue

        if not recording and not patch.getint('recording', 'record'):
            if debug>0:
                print "Recording is not enabled"
            time.sleep(1)

        if not recording and patch.getint('recording', 'record'):
            recording = True
            # open a new file
            fname = patch.getstring('recording', 'file')
            name, ext = os.path.splitext(fname)
            if len(ext) == 0:
                ext = '.' + fileformat
            fname = name + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext
            if debug>0:
                print "Recording enabled - opening", fname
            f = open(fname, 'w')
            f.write("event\tvalue\ttimestamp\n")
            f.flush()


except KeyboardInterrupt:
    if not f.closed:
        print 'Closing file'
        f.close()
    print 'Closing threads'
    for thread in trigger:
        thread.stop()
    r.publish('RECORDTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
