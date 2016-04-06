#!/usr/bin/env python

import sys
import os
import socket
import time
import threading
import redis
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import OSC          # see https://trac.v2.nl/wiki/pyOSC

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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Started OSC server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

try:
    s = OSC.OSCServer((config.get('osc','address'), config.getint('osc','port')))
    if debug>0:
        print "Started OSC server"
except:
    print "Unexpected error:", sys.exc_info()[0]
    print "Error: cannot start OSC server"
    exit()

# this is a list of OSC messages that are to be processed as button presses, i.e. using a pubsub message in redis
button_list = config.get('button', 'push').split(',')

# define a message-handler function for the server to call.
def forward_handler(addr, tags, data, source):
    print "---"
    print "source %s" % OSC.getUrlStr(source)
    print "addr   %s" % addr
    print "tags   %s" % tags
    print "data   %s" % data


    scale = EEGsynth.getfloat('processing', 'scale', config, r)
    if scale is None:
        scale = 1

    offset = EEGsynth.getfloat('processing', 'offset', config, r)
    if offset is None:
        offset = 0

    # apply the scale and offset
    for i in range(len(data)):
        data[i] = EEGsynth.rescale(data[i], scale, offset)

    # the results will be written to redis as "osc.1.faderA" etc.
    key = config.get('output', 'prefix') + addr.replace('/', '.')

    if tags=='f' or tags=='i':
        # it is a single value
        val = data[0]
        r.set(key, val)             # send it as control value
        if addr in button_list:
            r.publish(key,val)      # send it as trigger

    else:
        # it is a list, send it as a list of control values
        val = data
        r.set(key, val)

s.noCallback_handler = forward_handler
s.addDefaultHandlers()
# s.addMsgHandler("/1/faderA", test_handler)

# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
	print addr

# start the server thread
print "\nStarting module. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()

# loop while threads are running
try:
	while True:
		time.sleep(10)

except KeyboardInterrupt:
	print "\nClosing module."
	s.close()
	print "Waiting for Server-thread to finish."
	st.join()
	print "Done."
