#!/usr/bin/env python

# InputOSC records OSC data to Redis
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

import configparser
import argparse
import os
import redis
import socket
import sys
import threading
import time

# The required package depends on the Python version, one works for older and the other for newer versions.
# This cannot be handled easily by setup.py during installation, hence we only _try_ to load the module.
if sys.version_info < (3,5):
    try:
        import OSC
        use_old_version = True
    except ImportError:
        # give a warning, not an error, so that eegsynth.py does not fail as a whole
        print('Warning: OSC is required for the outputosc module, please install it with "pip install OSC"')
else:
    try:
        from pythonosc import dispatcher
        from pythonosc import osc_server
        use_old_version = False
    except ModuleNotFoundError:
        # give a warning, not an error, so that eegsynth.py does not fail as a whole
        print('Warning: pythonosc is required for the outputosc module, please install it with "pip install pythonosc"')

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
sys.path.insert(0, os.path.join(path, '../../lib'))
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
debug       = patch.getint('general', 'debug')
osc_address = patch.getstring('osc', 'address', default=socket.gethostbyname(socket.gethostname()))
osc_port    = patch.getint('osc', 'port')
prefix      = patch.getstring('output', 'prefix')

# the scale and offset are used to map OSC values to Redis values
output_scale    = patch.getfloat('output', 'scale', default=1)
output_offset   = patch.getfloat('output', 'offset', default=0)

# the server will call the message handler function upon incoming messages
def python2_message_handler(addr, tags, data, source):
    global prefix
    global output_scale
    global output_offset

    monitor.debug("---")
    monitor.debug("source %s" % OSC.getUrlStr(source))
    monitor.debug("addr   %s" % addr)
    monitor.debug("tags   %s" % tags)
    monitor.debug("data   %s" % data)

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

# the server will call the message handler function upon incoming messages
def python3_message_handler(addr, data):
    global prefix
    global output_scale
    global output_offset

    monitor.debug("addr   %s" % addr)
    monitor.debug("data   %s" % data)

    # assume that it is a single scalar value
    key = prefix + addr.replace('/', '.')
    val = EEGsynth.rescale(data, slope=output_scale, offset=output_offset)
    patch.setvalue(key, val)

try:
    if use_old_version:
        s = OSC.OSCServer((osc_address, osc_port))
        s.noCallback_handler = python2_message_handler
        # s.addMsgHandler("/1/faderA", test_handler)
        s.addDefaultHandlers()
        # just checking which handlers we have added
        monitor.info("Registered Callback functions are :")
        for addr in s.getOSCAddressSpace():
            monitor.info(addr)
        # start the server thread
        st = threading.Thread(target=s.serve_forever)
        st.start()
    else:
        dispatcher = dispatcher.Dispatcher()
        # dispatcher.map("/1/faderA", test_handler)
        dispatcher.set_default_handler(python3_message_handler)
        server = osc_server.ThreadingOSCUDPServer((osc_address, osc_port), dispatcher)
        monitor.info("Serving on {}".format(server.server_address))
        # the following is blocking
        server.serve_forever()
    monitor.success("Started OSC server")
except:
    raise RuntimeError("cannot start OSC server")

# keep looping while incoming OSC messages are being handled
# the code will never get here when using pythonosc with Python3, since that is blocking
try:
    while True:
        monitor.loop()
        time.sleep(patch.getfloat('general','delay'))
        # update the scale and offset
        output_scale    = patch.getfloat('output', 'scale', default=1)
        output_offset   = patch.getfloat('output', 'offset', default=0)

except KeyboardInterrupt:
    monitor.success("\nClosing module.")
    s.close()
    monitor.info("Waiting for OSC server thread to finish.")
    st.join()
    monitor.success("Done.")
