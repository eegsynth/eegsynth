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

import time


###################################################################################################
class client():
    def __init__(self):
        return

    def set(self, key, val):
        return 'OK'

    def get(self, key):
        return None

    def publish(self, key, val):
        return 'OK'

    def pubsub(self):
        return pubsub()

    def exists(self, key):
        return False


###################################################################################################
class pubsub():
    def __init__(self):
        pass

    def subscribe(self, channel):
        pass

    def listen(self):
        time.sleep(1)
        return []
