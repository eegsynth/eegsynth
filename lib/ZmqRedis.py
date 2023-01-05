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

import zmq
import threading

###################################################################################################
class server():
    def __init__(self, port=5555):
        context = zmq.Context()
        command = context.socket(zmq.REP)
        command.bind("tcp://*:%d" % (port+0))  # this is the socket for most commands
        publish = context.socket(zmq.PUB)
        publish.bind("tcp://*:%d" % (port+1))  # this is the socket for publishing
        self.command = command
        self.publish = publish
        self.store = {}
        self.debug = 1

    def start(self):
        while True:
            message = self.command.recv_string()
            cmd, key = message.split(' ', 1)
            if cmd == 'SET':
                if self.debug>1:
                    print(message)
                key, val = key.split(' ', 1)
                self.store[key] = val
                self.command.send_string('OK')
            elif cmd == 'GET':
                if self.debug>1:
                    print(message)
                if key in self.store:
                    self.command.send_string(self.store[key])
                else:
                    self.command.send_string('')
            elif cmd == 'PUBLISH':
                if self.debug>0:
                    print(message)
                key, val = key.split(' ', 1)
                self.command.send_string('OK')
                self.publish.send_string('%s %s' % (key, val))
            elif cmd == 'EXISTS':
                if self.debug>2:
                    print(message)
                if key in self.store.keys():
                    self.command.send_string('1')
                else:
                    self.command.send_string('0')


###################################################################################################
class client():
    def __init__(self, host='localhost', port=5555):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://%s:%d" % (host, port))
        self.socket = socket
        self.debug = 0
        self.lock = threading.Lock()

    def pubsub(self):
        return pubsub()

    def set(self, key, val):
        if self.debug>0:
            print("SET %s %f" % (key, val))
        with self.lock:
            self.socket.send_string("SET %s %f" % (key, val))
            status = self.socket.recv_string()
        return
        
    def get(self, key):
        if self.debug>0:
            print("GET %s" % key)
        with self.lock:
            self.socket.send_string("GET %s" % key)
            val = self.socket.recv_string()
        if len(val)==0:
            return None
        else:
            return val

    def publish(self, key, val):
        if self.debug>0:
            print("PUBLISH %s %f" % (key, val))
        with self.lock:
            self.socket.send_string("PUBLISH %s %f" % (key, val))
            status = self.socket.recv_string()
        return status

    def exists(self, key):
        with self.lock:
            self.socket.send_string("EXISTS %s" % key)
            val = bool(float(self.socket.recv_string()))
        return val
        

###################################################################################################
class pubsub():
    def __init__(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")
        self.socket = socket

    def subscribe(self, channel):
        self.socket.setsockopt_string(zmq.SUBSCRIBE, channel)

    def listen(self):
        message = self.socket.recv_string()
        key, val = message.split()
        item = {}
        item['type'] = 'message'
        item['channel'] = key
        item['data'] = val
        return [item]


###################################################################################################
if __name__ == "__main__":
    r = server()
    r.start()
