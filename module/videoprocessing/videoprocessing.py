#!/usr/bin/env python3

# Videoprocessing module for live processing of video and webcam data
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019-2023 EEGsynth project
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

import numpy as np
import os
import sys
import time
import cv2

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


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint('general', 'debug', default=1))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global device, prefix, cap, frame, frame_height, frame_width, frame_depth, previous

    # get the options from the configuration file
    device = patch.getint('input', 'device', default=0)
    prefix = patch.getstring('output', 'prefix')

    cap = cv2.VideoCapture(device)

    # read a single frame to determine the characteristics
    ret, frame = cap.read()

    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    frame_depth = frame.shape[2]

    # remember the frame for the next iteration
    previous = frame

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global device, prefix, cap, frame, frame_height, frame_width, frame_depth, previous

    # Capture frame-by-frame
    ret, frame = cap.read()

    bottom = patch.getfloat('crop', 'bottom', default=1)
    top    = patch.getfloat('crop', 'top', default=frame_height)
    left   = patch.getfloat('crop', 'left', default=1)
    right  = patch.getfloat('crop', 'right', default=frame_width)

    if top <= 1 or bottom <= 1 or left <= 1 or right <= 1:
        # assume values between 0 and 1
        bottom = int(bottom * frame_height)
        top    = int(top * frame_height)
        left   = int(left * frame_width + 1)
        right  = int(right * frame_width + 1)
    else:
        # assume values that correspond to pixels
        bottom = int(bottom)
        top    = int(top)
        left   = int(left)
        right  = int(right)

    masked = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = masked.astype('float') / 2
    masked = masked.astype('uint8')
    masked = np.stack((masked, masked, masked), 2)

    # crop the image frame
    x1 = frame_height - top
    x2 = frame_height - bottom + 1
    y1 = left - 1
    y2 = right

    cropped = frame[x1:x2, y1:y2, :]
    masked[x1:x2, y1:y2, :] = cropped

    # display the masked frame
    cv2.imshow('frame', masked)

    if frame.shape[0] > 0 and frame.shape[1] > 0:
        # default order is blue, green, red
        bgr = cropped
        key = '%s.level.blue' % (prefix)
        val = np.mean(bgr[0].flatten())
        patch.setvalue(key, val)
        key = '%s.level.green' % (prefix)
        val = np.mean(bgr[1].flatten())
        patch.setvalue(key, val)
        key = '%s.level.red' % (prefix)
        val = np.mean(bgr[2].flatten())
        patch.setvalue(key, val)

        # convert to HSV
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        key = '%s.level.hue' % (prefix)
        val = np.mean(hsv[0].flatten())
        patch.setvalue(key, val)
        key = '%s.level.saturation' % (prefix)
        val = np.mean(hsv[1].flatten())
        patch.setvalue(key, val)
        key = '%s.level.value' % (prefix)
        val = np.mean(hsv[2].flatten())
        patch.setvalue(key, val)

        # convert to grey
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        key = '%s.level.grey' % (prefix)
        val = np.mean(grey.flatten())
        patch.setvalue(key, val)

        if not previous is None:
            # compute the features of the difference between this and previous frame
            difference = frame.astype('float')-previous.astype('float')
            cropped = difference[x1:x2, y1:y2, :]

            bgr = cropped
            key = '%s.difference.blue' % (prefix)
            val = np.mean(bgr[0].flatten())
            patch.setvalue(key, val)
            key = '%s.difference.green' % (prefix)
            val = np.mean(bgr[1].flatten())
            patch.setvalue(key, val)
            key = '%s.difference.red' % (prefix)
            val = np.mean(bgr[2].flatten())
            patch.setvalue(key, val)

    # remember the frame for the next iteration
    previous = frame

    if cv2.waitKey(1) == ord('q'):
        raise(KeyboardInterrupt)

def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor
    while True:
        monitor.loop()
        _loop_once()


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, cap
    cap.release()
    cv2.destroyAllWindows()
    monitor.success('Disconnected from input FieldTrip buffer')


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
