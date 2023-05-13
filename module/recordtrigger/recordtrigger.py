#!/usr/bin/env python

# This module records Redis messages (i.e. triggers) to a TSV file
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2018-2022 EEGsynth project
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

import datetime
import os
import sys
import time
import threading
import tempfile

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
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


class TriggerThread(threading.Thread):
    def __init__(self, redischannel):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        global r, monitor, lock
        global f, csvwriter
        pubsub = patch.pubsub()
        pubsub.subscribe('RECORDTRIGGER_UNBLOCK')  # this message unblocks the Redis listen command
        pubsub.subscribe(self.redischannel)        # this message triggers the event
        while self.running:
            for item in pubsub.listen():
                timestamp = datetime.datetime.now().isoformat()
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] == self.redischannel:
                    val = item["data"]
                    # the trigger value should be saved
                    if input_scale != None or input_offset != None:
                        try:
                            # convert it to a number and apply the scaling and the offset
                            val = float(val)
                            val = EEGsynth.rescale(val, slope=input_scale, offset=input_offset)
                        except ValueError:
                            # keep it as a string
                            monitor.info(("cannot apply scaling, writing %s as string" % (self.redischannel)))
                    if f and not f.closed:
                        # write the value, it can be either a number or a string
                        with lock:
                            csvwriter.writerow([self.redischannel, val, timestamp])
                        monitor.info(("%s\t%s\t%s" % (self.redischannel, val, timestamp)))


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global delay, input_scale, input_offset, filename, fileformat, f, recording, filenumber, lock, trigger, item, thread

    # get the options from the configuration file
    delay = patch.getfloat('general', 'delay')
    input_scale = patch.getfloat('input', 'scale', default=None)
    input_offset = patch.getfloat('input', 'offset', default=None)
    filename = patch.getstring('recording', 'file')
    fileformat = patch.getstring('recording', 'format')

    if fileformat is None:
        # determine the file format from the file name
        name, ext = os.path.splitext(filename)
        fileformat = ext[1:]

    # start with a temporary file which is immediately closed
    f = tempfile.TemporaryFile().close()
    recording = False
    filenumber = 0

    # this is to prevent two triggers from being saved at the same time
    lock = threading.Lock()

    # create the background threads that deal with the triggers
    trigger = []
    monitor.info("Setting up threads for each trigger")
    for item in patch.config.items('trigger'):
        trigger.append(TriggerThread(item[0]))
        monitor.debug(item[0] + ' = OK')

    # start the thread for each of the triggers
    for thread in trigger:
        thread.start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global delay, input_scale, input_offset, filename, fileformat, recording, filenumber, lock, trigger, item, thread
    global fname, ext, f, csvwriter

    if recording and not patch.getint('recording', 'record'):
        monitor.info("Recording disabled - closing " + fname)
        f.close()
        recording = False
        return

    if not recording and not patch.getint('recording', 'record'):
        monitor.info("Recording is not enabled")
        time.sleep(1)

    if not recording and patch.getint('recording', 'record'):
        recording = True
        # open a new file
        name, ext = os.path.splitext(filename)
        if len(ext) == 0:
            ext = '.' + fileformat
        fname = name + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext
        monitor.info("Recording enabled - opening " + fname)
        
        f = open(fname, 'w')
        if fileformat == 'csv':
            csvwriter = csv.writer(f, delimiter=',')
        elif fileformat == 'tsv':
            csvwriter = csv.writer(f, delimiter='\t')
        csvwriter.writeheader(["event", "value", "timestamp"])
        f.flush()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop(*args):
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, patch, trigger, recording, fname, f
    if recording:
        recording = False
        monitor.info("Closing " + fname)
        f.close()
    monitor.success('Closing threads')
    for thread in trigger:
        thread.stop()
    patch.publish('RECORDTRIGGER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
