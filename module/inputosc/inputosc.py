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

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, 'inputosc.ini'))

r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
try:
    response = r.client_list()
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

s = OSC.OSCServer((config.get('osc','address'), config.getint('osc','port')))

# define a message-handler function for the server to call.
def forward_handler(addr, tags, data, source):
    print "---"
    print "source %s" % OSC.getUrlStr(source)
    print "addr   %s" % addr
    print "tags   %s" % tags
    print "data   %s" % data
    # prefix.addr=value
    key = config.get('output', 'prefix')+addr.replace('/', '.')
    if tags=='f' or tags=='i':
        # send it as a single value
        val = data[0]
        r.set(key, val)
    else:
        # send it as a list
        val = data
        r.set(key, val)

s.noCallback_handler = forward_handler
s.addDefaultHandlers()
# s.addMsgHandler("/1/faderD", test_handler)

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
