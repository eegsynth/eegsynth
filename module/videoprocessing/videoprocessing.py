#!/usr/bin/env python3

# Videoprocessing module for live processing of video and webcam data
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2019 EEGsynth project
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
import numpy as np
import os
import redis
import sys
import time
import cv2
from pgmagick import Image

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
elif sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
else:
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(path, os.path.splitext(file)[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis', 'hostname'), port=config.getint('redis', 'port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    raise RuntimeError("cannot connect to Redis server")

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this can be used to show parameters that have changed
monitor = EEGsynth.monitor()

# get the options from the configuration file
debug = patch.getint('general', 'debug')

prefix = patch.getstring('output', 'prefix')
output_scale = patch.getfloat('output', 'scale', default=1. / 255)
output_offset = patch.getfloat('output', 'offset', default=0.)

cap = cv2.VideoCapture(0)

ret, frame = cap.read()
frame_height = frame.shape[0]
frame_width = frame.shape[1]
frame_depth = frame.shape[2]

previous = None

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    bottom = patch.getfloat('crop', 'bottom', default=1)
    top = patch.getfloat('crop', 'top', default=frame_height)
    left = patch.getfloat('crop', 'left', default=1)
    right = patch.getfloat('crop', 'right', default=frame_width)

    if top <= 1 or bottom <= 1 or left <= 1 or right <= 1:
        # assume values between 0 and 1
        bottom = int(bottom * frame_height)
        top = int(top * frame_height)
        left = int(left * frame_width + 1)
        right = int(right * frame_width + 1)
    else:
        # assume values that correspond to pixels
        bottom = int(bottom)
        top = int(top)
        left = int(left)
        right = int(right)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = gray.astype('float') / 2
    mask = mask.astype('uint8')
    mask = np.stack((mask, mask, mask), 2)

    # crop the image frame by making a masked version
    x1 = frame_height - top
    x2 = frame_height - bottom + 1
    y1 = left - 1
    y2 = right

    section  = frame[x1:x2, y1:y2, :]
    mask[x1:x2, y1:y2, :] = section
    debug = 0

    if frame.shape[0] > 0 and frame.shape[1] > 0:
        # default order is blue, green, red
        bgr = section
        key = '%s.level.blue' % (prefix)
        val = EEGsynth.rescale(np.mean(bgr[0].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=1)
        key = '%s.level.green' % (prefix)
        val = EEGsynth.rescale(np.mean(bgr[1].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)
        key = '%s.level.red' % (prefix)
        val = EEGsynth.rescale(np.mean(bgr[2].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)

        # convert to HSV
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        key = '%s.level.hue' % (prefix)
        val = EEGsynth.rescale(np.mean(hsv[0].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)
        key = '%s.level.saturation' % (prefix)
        val = EEGsynth.rescale(np.mean(hsv[1].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)
        key = '%s.level.value' % (prefix)
        val = EEGsynth.rescale(np.mean(hsv[2].flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)

        # convert to grey
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        key = '%s.level.grey' % (prefix)
        val = EEGsynth.rescale(np.mean(grey.flatten()), slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)

        if not previous is None:
            # compute the features of the difference between this and previous frame
            difference = frame.astype('float')-previous.astype('float')
            section = difference[x1:x2, y1:y2, :]

            bgr = section
            key = '%s.difference.blue' % (prefix)
            val = EEGsynth.rescale(np.mean(bgr[0].flatten()), slope=output_scale, offset=output_offset)
            patch.setvalue(key, val, debug=debug)
            key = '%s.difference.green' % (prefix)
            val = EEGsynth.rescale(np.mean(bgr[1].flatten()), slope=output_scale, offset=output_offset)
            patch.setvalue(key, val, debug=debug)
            key = '%s.difference.red' % (prefix)
            val = EEGsynth.rescale(np.mean(bgr[2].flatten()), slope=output_scale, offset=output_offset)
            patch.setvalue(key, val, debug=debug)

    # remember the frame for the next iteration
    previous = frame

    # display the masked frame
    cv2.imshow('frame', mask)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
