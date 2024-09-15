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

import threading
import time

store = {}
latest = None


###################################################################################################
class client():
    def __init__(self):
        store = {}

    def set(self, key, val):
        global store, latest
        store[key] = val
        return

    def get(self, key):
        global store, latest
        if key in store:
            return store[key]
        else:
            return None

    def publish(self, key, val):
        global store, latest
        store[key] = val
        latest = key

    def pubsub(self):
        return pubsub()

    def exists(self, key):
        return key in store

###################################################################################################
class pubsub():
    def __init__(self):
        self.subscribed = []

    def subscribe(self, key):
        self.subscribed.append(key)

    def listen(self):
        global store, latest
        while not latest in self.subscribed:
            time.sleep(0.1)
        item = dict()
        item['type'] = 'message'
        item['channel'] = latest
        item['data'] = store[latest]
        latest = None
        return [item]
