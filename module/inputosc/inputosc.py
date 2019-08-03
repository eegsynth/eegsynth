#!/usr/bin/env python

# InputOSC records OSC data to Redis
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2019 EEGsynth project
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
import OSC          # see https://trac.v2.nl/wiki/pyOSC
import argparse
import os
import redis
import socket
import sys
import threading
import time

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
elif sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
else:
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print("Error: cannot connect to redis server")
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# get the options from the configuration file
debug       = patch.getint('general', 'debug')
osc_address = patch.getstring('osc', 'address', default=socket.gethostbyname(socket.gethostname()))
osc_port    = patch.getint('osc', 'port')
prefix      = patch.getstring('output', 'prefix')
delay       = patch.getfloat('general', 'delay', default=0.05)

# the scale and offset are used to map OSC values to Redis values
output_scale    = patch.getfloat('output', 'scale', default=1)
output_offset   = patch.getfloat('output', 'offset', default=0)

try:
    s = OSC.OSCServer((osc_address, osc_port))
    if debug > 0:
        print("Started OSC server")
except:
    print("Unexpected error:", sys.exc_info()[0])
    print("Error: cannot start OSC server")
    exit()

# define a message-handler function that the server will call upon incoming messages
def forward_handler(addr, tags, data, source):
    global prefix
    global output_scale
    global output_offset

    if debug > 1:
        print("---")
        print("source %s" % OSC.getUrlStr(source))
        print("addr   %s" % addr)
        print("tags   %s" % tags)
        print("data   %s" % data)

    if addr[0] != '/':
        # ensure it starts with a slash
        addr = '/' + addr

    if tags == 'f' or tags == 'i':
        # it is a single scalar value
        key = prefix + addr.replace('/', '.')
        val = EEGsynth.rescale(data[0], slope=output_scale, offset=output_offset)
        patch.setvalue(key, val)

    else:
        for i in range(len(data)):
            # it is a list, send it as multiple scalar control values
            # append the index to the key, this starts with 1
            key = prefix + addr.replace('/', '.') + '.%i' % (i+1)
            val = EEGsynth.rescale(data[i], slope=output_scale, offset=output_offset)
            patch.setvalue(key, val)


s.noCallback_handler = forward_handler
s.addDefaultHandlers()
# s.addMsgHandler("/1/faderA", test_handler)

# just checking which handlers we have added
print("Registered Callback functions are :")
for addr in s.getOSCAddressSpace():
    print(addr)

# start the server thread
st = threading.Thread(target=s.serve_forever)
st.start()

# keep looping while incoming OSC messages are being handled
try:
    while True:
        time.sleep(delay)
        # the scale and offset are used to map OSC values to Redis values
        output_scale    = patch.getfloat('output', 'scale', default=1)
        output_offset   = patch.getfloat('output', 'offset', default=0)

except KeyboardInterrupt:
    print("\nClosing module.")
    s.close()
    print("Waiting for OSC server thread to finish.")
    st.join()
    print("Done.")
