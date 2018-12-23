#!/usr/bin/env python

# InputOSC records OSC data to Redis
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

import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import OSC          # see https://trac.v2.nl/wiki/pyOSC
import argparse
import os
import redis
import socket
import sys
import threading
import time

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
del config

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')

try:
    s = OSC.OSCServer((patch.getstring('osc', 'address'), patch.getint('osc', 'port')))
    if debug > 0:
        print "Started OSC server"
except:
    print "Unexpected error:", sys.exc_info()[0]
    print "Error: cannot start OSC server"
    exit()

# this is a list of OSC messages that are to be processed as button presses, i.e. using a pubsub message in redis
button_list = patch.getstring('button', 'push', multiple=True)

# the scale and offset are used to map OSC values to Redis values
scale = patch.getfloat('output', 'scale', default=1)
offset = patch.getfloat('output', 'offset', default=0)

# the results will be written to redis as "osc.1.faderA" etc.
prefix = patch.getstring('output', 'prefix')

# the scale, offset and prefix are updated every N seconds
update = patch.getfloat('general', 'update', default=1)


# define a message-handler function that the server will call upon incoming messages
def forward_handler(addr, tags, data, source):
    global prefix
    global scake
    global offset

    if debug > 1:
        print "---"
        print "source %s" % OSC.getUrlStr(source)
        print "addr   %s" % addr
        print "tags   %s" % tags
        print "data   %s" % data

    if addr[0] != '/':
        # ensure it starts with a slash
        addr = '/' + addr

    if tags == 'f' or tags == 'i':
        # it is a single value
        key = prefix + addr.replace('/', '.')
        val = EEGsynth.rescale(data[0], slope=scale, offset=offset)
        patch.setvalue(key, val)

    else:
        for i in range(len(data)):
            # it is a list, send it as multiple scalar control values
            # append the index to the key, this starts with 0
            key = prefix + addr.replace('/', '.') + '.%i' % i
            val = EEGsynth.rescale(data[i], slope=scale, offset=offset)
            patch.setvalue(key, val)


s.noCallback_handler = forward_handler
s.addDefaultHandlers()
# s.addMsgHandler("/1/faderA", test_handler)

# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
    print addr

# start the server thread
print "\nStarting module. Use ctrl-C to quit."
st = threading.Thread(target=s.serve_forever)
st.start()

# loop while incoming OSC messages are being handled
try:
    while True:
        time.sleep(update)
        # the scale and offset are used to map OSC values to Redis values
        scale = patch.getfloat('output', 'scale', default=1)
        offset = patch.getfloat('output', 'offset', default=0)
        # the results will be written to redis as "osc.1.faderA" etc.
        prefix = patch.getstring('output', 'prefix')

except KeyboardInterrupt:
    print "\nClosing module."
    s.close()
    print "Waiting for Server-thread to finish."
    st.join()
    print "Done."
