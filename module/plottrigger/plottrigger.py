#!/usr/bin/env python

# Plottrigger plots discrete events along a timeline that is continuously scrolling
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2018 EEGsynth project
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

from pyqtgraph.Qt import QtGui, QtCore
import ConfigParser  # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import argparse
import numpy as np
import os
import pyqtgraph as pg
import sys
import time
import threading
import signal

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
import FieldTrip

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

# this determines how much debugging information gets printed
debug       = patch.getint('general', 'debug')
delay       = patch.getfloat('general', 'delay')            # in seconds
window      = patch.getfloat('general', 'window')           # in seconds
value       = patch.getint('general', 'value', default=0)   # boolean
winx        = patch.getfloat('display', 'xpos')
winy        = patch.getfloat('display', 'ypos')
winwidth    = patch.getfloat('display', 'width')
winheight   = patch.getfloat('display', 'height')

# Initialize variables
data = {}

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, number):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.number = number
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('PLOTTRIGGER_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)      # this message contains the note
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel']==self.redischannel:
                    if debug>1:
                        print item
                    lock.acquire()
                    now = time.time()
                    val = float(item['data'])
                    # append the time and value as a tuple
                    data[self.number].append((now, val))
                    lock.release()

gate = []
number = []
# each of the gates that can be triggered is mapped onto a different message
for i in range(1, 17):
    name = 'channel{}'.format(i)
    if config.has_option('gate', name):
        number.append(i)
        data[i] = []
        # start the background thread that deals with this channel
        this = TriggerThread(patch.getstring('gate', name), i)
        gate.append(this)
        if debug>1:
            print name, 'OK'

# start the thread for each of the notes
for thread in gate:
    thread.start()


# initialize graphical window
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="EEGsynth plottrigger")
win.setWindowTitle('EEGsynth plottrigger')
win.setGeometry(winx, winy, winwidth, winheight)

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

plot = win.addPlot()
plot.setLabel('left', text='Channel')
plot.setLabel('bottom', text='Time (s)')
plot.setXRange(-window, 0)
plot.setYRange(0.5, len(gate)+0.5)

def update():
    now = time.time()
    plot.clear()
    for y in number:
        for event in data[y]:
            x = event[0] - now      # time
            v = event[1]            # value

            if x < -window-0.5:
                # remove the event if it is too far in the past
                data[y].remove(event)
                continue

            scatter = pg.ScatterPlotItem()
            scatter.addPoints([{'pos': (x, y)}])
            plot.addItem(scatter)

            if value:
                # show the numeric value next to the trigger

                if abs(v-round(v))<0.001:
                    # print it as integer value
                    s = '%d' % v
                else:
                    # print it as floating point value
                    s = '%2.1f' % v

                text = pg.TextItem(s, anchor=(0,0))
                text.setPos(x, y)
                plot.addItem(text)

# keyboard interrupt handling
def sigint_handler(*args):
    QtGui.QApplication.quit()

signal.signal(signal.SIGINT, sigint_handler)

# Set timer for update
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.setInterval(10)                     # timeout in milliseconds
timer.start(int(round(delay * 1000)))     # in milliseconds

# Start
QtGui.QApplication.instance().exec_()

print 'Closing threads'
for thread in gate:
    thread.stop()
r.publish('PLOTTRIGGER_UNBLOCK', 1)
for thread in gate:
    thread.join()
