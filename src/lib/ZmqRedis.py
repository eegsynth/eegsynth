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
        self.debug = 0

    def start(self):
        while True:
            message = self.command.recv_string()
            if message.startswith('SET'):
                if self.debug>1:
                    print(message)
                cmd, key, val = message.split(' ', 2)
                self.store[key] = val
                self.command.send_string('OK')

            elif message.startswith('GET'):
                if self.debug>2:
                    print(message)
                cmd, key = message.split(' ', 1)
                if key in self.store:
                    self.command.send_string(self.store[key])
                else:
                    self.command.send_string('')

            elif message.startswith('PUBLISH'):
                if self.debug>1:
                    print(message)
                cmd, key, val = message.split(' ', 2)
                self.command.send_string('OK')
                self.publish.send_string('%s %s' % (key, val))

            elif message.startswith('KEYS'):
                if self.debug>1:
                    print(message)
                cmd, pattern = message.split(' ', 1)
                keys = list(self.store.keys())
                if pattern == '*':
                    # return all keys
                    self.command.send_string(' '.join(keys))
                elif pattern.startswith('*'):
                    # return all keys that start with anything and end with the pattern
                    sel = [i.endswith(pattern[1:]) for i in keys]
                    keys = [i for i,b in zip(keys, sel) if b]
                    self.command.send_string(' '.join(keys))
                elif pattern.endswith('*'):
                    # return all keys that start with the pattern and end with anything
                    sel = [i.startswith(pattern[:-1]) for i in keys]
                    keys = [i for i,b in zip(keys, sel) if b]
                    self.command.send_string(' '.join(keys))
                else:
                    # return no keys
                    self.command.send_string('')

            elif message.startswith('EXISTS'):
                if self.debug>1:
                    print(message)
                cmd, key = message.split(' ', 1)
                if key in self.store.keys():
                    self.command.send_string('1')
                else:
                    self.command.send_string('0')

            elif message.startswith('CONNECT'):
                if self.debug>0:
                    print(message)
                self.command.send_string('1')


###################################################################################################
class client():
    def __init__(self, host='localhost', port=5555, timeout=5000):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.RCVTIMEO = timeout # in milliseconds
        socket.connect("tcp://%s:%d" % (host, port))
        self.socket = socket
        self.debug = 0
        self.timeout = timeout
        self.lock = threading.Lock()

    def pubsub(self):
        return pubsub()

    def set(self, key, val):
        if self.debug>0:
            if isinstance(val, str):
                print("SET %s %s" % (key, val))
            else:
                print("SET %s %f" % (key, val))
        with self.lock:
            if isinstance(val, str):
                self.socket.send_string("SET %s %s" % (key, val))
            else:
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
            if isinstance(val, str):
                print("PUBLISH %s %s" % (key, val))
            else:
                print("PUBLISH %s %f" % (key, val))
        with self.lock:
            if isinstance(val, str):
                self.socket.send_string("PUBLISH %s %s" % (key, val))
            else:
                self.socket.send_string("PUBLISH %s %f" % (key, val))
            status = self.socket.recv_string()
        return status

    def exists(self, key):
        with self.lock:
            self.socket.send_string("EXISTS %s" % key)
            val = bool(float(self.socket.recv_string()))
        return val

    def keys(self, pattern):
        with self.lock:
            self.socket.send_string("KEYS %s" % pattern)
            val = self.socket.recv_string()
            val = val.split(' ')
        return val

    def connect(self):
        # test whether this client is connected to the server
        with self.lock:
            try:
                self.socket.send_string("CONNECT")
                val = bool(float(self.socket.recv_string()))
            except:
                val = False
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
        key, val = message.split(' ', 1)
        item = {}
        item['type'] = 'message'
        item['channel'] = key
        item['data'] = val
        return [item]


###################################################################################################
if __name__ == "__main__":
    r = server()
    r.start()
