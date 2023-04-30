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
    file = os.path.split(__file__)[-1]
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

###########################################################################################

def process_frame(frame, downsample, contrast, brightness, mirror):
    global patch, monitor

    # downsample with the specified factor
    # see https://www.tutorialspoint.com/downsampling-an-image-using-opencv
    for step in range(downsample-1):
        frame = cv2.pyrDown(frame)

    # map the values between 0 and 1 such that 0.5 is neutral
    contrast = 3 ** ((contrast-0.5)*2)
    brightness = 2*(brightness-0.5)*127

    monitor.update('contrast', contrast)
    monitor.update('brightness', brightness)

    # apply contrast and brightness
    # see https://docs.opencv.org/3.4/d3/dc1/tutorial_basic_linear_transform.html
    frame = np.clip(contrast*frame.astype('float') + brightness, 0, 255)
    frame = frame.astype('uint8')

    # flip left and right
    if mirror:
        frame = np.flip(frame, axis=1)

    return frame

###########################################################################################

def mask_frame(frame, top, bottom, left, right):

    if len(frame.shape)==2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # make a grey version at half-intensity of the original frame
    masked = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = masked.astype('float') / 2
    masked = masked.astype('uint8')
    masked = np.stack((masked, masked, masked), 2)

    # count how many pixels there are in the cropped selection
    pixels = (bottom-top)*(right-left)

    # insert a cropped selection of the original frame in the mask
    masked[top:bottom, left:right, :] = frame[top:bottom, left:right, :]

    if pixels>0:
        # draw a rectangle, see https://www.tutorialspoint.com/draw-rectangle-on-an-image-using-opencv
        cv2.rectangle(masked, (left,top), (right,bottom), (0,0,255), 1)

    return masked

###########################################################################################

def weighted_position(frame):
    global patch, monitor

    if len(frame.shape)==3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    frame_height = frame.shape[0]
    frame_width = frame.shape[1]

    frame_as_row = np.mean(frame, axis=0, dtype=np.float, keepdims=False)
    frame_as_col = np.mean(frame, axis=1, dtype=np.float, keepdims=False)
    pixel_as_row = np.linspace(0, 1, frame_width)
    pixel_as_col = np.linspace(0, 1, frame_height)
    horizontal = np.multiply(frame_as_row, pixel_as_row)
    vertical = np.multiply(frame_as_col, pixel_as_col)
    horizontal = np.mean(horizontal)/np.mean(frame_as_row)
    vertical = np.mean(vertical)/np.mean(frame_as_col)

    return horizontal, vertical


###########################################################################################

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
    global device, title, prefix, show, downsample, contrast, brightness, mirror, cap, fps, frame, frame_height, frame_width, frame_depth, previous, previous_grey

    # get the options from the configuration file
    device = patch.getint('input', 'device', default=None)
    file = patch.getstring('input', 'file', default=None)
    title = patch.getstring('display', 'title', default='EEGsynth videoprocessing')
    prefix = patch.getstring('output', 'prefix')
    downsample = patch.getint('input', 'downsample', default=1)

    # these can change every frame
    contrast = patch.getfloat('input', 'contrast', default=0.5)
    brightness = patch.getfloat('input', 'brightness', default=0.5)
    show = patch.getstring('display', 'show', default='color')
    mirror = patch.getint('display', 'mirror', default=0)

    cap = None

    if not device==None:
        # open the webcam stream
        cap = cv2.VideoCapture(device)
        file = None
    elif not file==None:
        # open a video stream from file
        cap = cv2.VideoCapture(file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        monitor.info('fps = ', fps)
        monitor.info('length = ', length)
        device = None
    else:
        raise RuntimeError('You should specify a device or a file')

    # read a single frame to determine the characteristics
    ret, frame = cap.read()

    # do basic preprocessing on the input image
    frame = process_frame(frame, downsample, contrast, brightness, mirror)

    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    frame_depth = frame.shape[2]

    # remember this as the previous rame for the next iteration
    previous = frame
    previous_grey = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor
    global device, file, title, prefix, show, downsample, contrast, brightness, mirror, cap, frame, frame_height, frame_width, frame_depth, previous, previous_grey

    # these can change dynamically
    contrast = patch.getfloat('input', 'contrast', default=0.5)
    brightness = patch.getfloat('input', 'brightness', default=0.5)
    mirror = patch.getint('display', 'mirror', default=0)

    # capture frame-by-frame
    ret, frame = cap.read()

    if device==None and not ret:
        monitor.warning('rewind to the start of the video')
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        skip = True
    else:
        skip = False

    # downsample with the specified factor
    frame = process_frame(frame, downsample, contrast, brightness, mirror)

    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    frame_depth = frame.shape[2]

    top    = patch.getfloat('crop', 'top', default=1)
    bottom = patch.getfloat('crop', 'bottom', default=frame_height)
    left   = patch.getfloat('crop', 'left', default=1)
    right  = patch.getfloat('crop', 'right', default=frame_width)

    if top <= 1 or bottom <= 1 or left <= 1 or right <= 1:
        # assume values between 0 and 1
        top    = int((1-top) * frame_height)+1
        bottom = int((1-bottom) * frame_height)+1
        left   = int(left * frame_width)+1
        right  = int(right * frame_width)+1
    else:
        # assume values that correspond to pixels
        top    = int(top)
        bottom = int(bottom)
        left   = int(left)
        right  = int(right)

    monitor.update('top', top)
    monitor.update('bottom', bottom)
    monitor.update('left', left)
    monitor.update('right', right)

    if top>bottom:
        top=bottom

    if left>right:
        left=right

    # count how many pixels there are in the cropped selection
    pixels = (bottom-top)*(right-left)

    # convert to grey
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # which metrics to compute, we don't want these flags to change during the loop
    metrics_color = patch.getint('metrics', 'color', default=1)
    metrics_grey = patch.getint('metrics', 'grey', default=1)
    metrics_diff = patch.getint('metrics', 'diff', default=1)
    metrics_edge = patch.getint('metrics', 'edge', default=1)
    metrics_flow = patch.getint('metrics', 'flow', default=1)

    # only do the following metric computations when needed

    if metrics_diff or show=='diff':
        # compute the difference between this and the previous frame
        diff = cv2.absdiff(frame, previous)

    if metrics_edge or show=='edge':
        # do edge detection
        edge = cv2.Canny(frame, 85, 170) # thresholds at 1/3 and 2/3 of 255

    if metrics_flow or show=='flow':
        # do optical flow detection
        flow = cv2.calcOpticalFlowFarneback(previous_grey, grey, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    if show=='color':
        masked = mask_frame(frame, top, bottom, left, right)
    elif show=='grey':
        masked = mask_frame(grey, top, bottom, left, right)
    elif show=='diff':
        masked = mask_frame(diff, top, bottom, left, right)
    elif show=='edge':
        masked = mask_frame(edge, top, bottom, left, right)
    elif show=='flow':
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_hsv = np.zeros_like(frame)
        flow_hsv[..., 0] = ang*180/np.pi/2
        flow_hsv[..., 1] = 255
        flow_hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        flow_bgr = cv2.cvtColor(flow_hsv, cv2.COLOR_HSV2BGR)
        masked = mask_frame(flow_bgr, top, bottom, left, right)

    # display the masked image
    cv2.imshow(title, masked)

    if pixels==0:
        monitor.warning('the cropped image is empty')

    elif skip:
        # skip the processing of the first frame immediately following a rewind
        pass

    else:
        ####################################################################
        # do the processing of the color

        if metrics_color:
            # the default order is blue, green, red
            bgr = frame[top:bottom, left:right, :]

            key = '%s.blue' % (prefix)
            val = np.mean(bgr[:,:,0].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.green' % (prefix)
            val = np.mean(bgr[:,:,1].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.red' % (prefix)
            val = np.mean(bgr[:,:,2].flatten())/255.
            patch.setvalue(key, val)

            # convert to HSV
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

            key = '%s.hue' % (prefix)
            val = np.mean(hsv[:,:,0].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.saturation' % (prefix)
            val = np.mean(hsv[:,:,1].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.value' % (prefix)
            val = np.mean(hsv[:,:,2].flatten())/255.
            patch.setvalue(key, val)

        ####################################################################
        # do the processing of the grey

        if metrics_grey:
            # convert the cropped image to grey
            grey = cv2.cvtColor(frame[top:bottom, left:right, :], cv2.COLOR_BGR2GRAY)

            key = '%s.grey' % (prefix)
            val = np.mean(grey.flatten())/255.
            patch.setvalue(key, val)

            # compute the position of the center-of-mass
            horizontal, vertical = weighted_position(grey)
            key = '%s.grey.horizontal' % (prefix)
            patch.setvalue(key, horizontal)
            key = '%s.grey.vertical' % (prefix)
            patch.setvalue(key, 1-vertical)

        ####################################################################
        # do the processing of the color difference

        if metrics_diff:
            # the default order is blue, green, red
            bgr = diff[top:bottom, left:right, :]

            key = '%s.diff.blue' % (prefix)
            val = np.mean(bgr[:,:,0].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.diff.green' % (prefix)
            val = np.mean(bgr[:,:,1].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.diff.red' % (prefix)
            val = np.mean(bgr[:,:,2].flatten())/255.
            patch.setvalue(key, val)

            # convert to HSV
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

            key = '%s.diff.hue' % (prefix)
            val = np.mean(hsv[:,:,0].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.diff.saturation' % (prefix)
            val = np.mean(hsv[:,:,1].flatten())/255.
            patch.setvalue(key, val)
            key = '%s.diff.value' % (prefix)
            val = np.mean(hsv[:,:,2].flatten())/255.
            patch.setvalue(key, val)

        ####################################################################
        # do the processing of the grey difference

        if metrics_diff and metrics_grey:
            # convert the cropped difference to grey
            grey = cv2.cvtColor(diff[top:bottom, left:right, :], cv2.COLOR_BGR2GRAY)

            key = '%s.diff.grey' % (prefix)
            val = np.mean(grey.flatten())/255.
            patch.setvalue(key, val)

            # compute the position of the center-of-mass
            horizontal, vertical = weighted_position(grey)
            key = '%s.diff.grey.horizontal' % (prefix)
            patch.setvalue(key, horizontal)
            key = '%s.diff.grey.vertical' % (prefix)
            patch.setvalue(key, 1-vertical)

        ####################################################################
        # the following section implements the processing of the edges

        if metrics_edge:
            # crop the image with the edges, it is already grey
            grey = edge[top:bottom, left:right]

            key = '%s.edge' % (prefix)
            val = np.mean(grey.flatten())/255.
            patch.setvalue(key, val)

            # compute the position of the center-of-mass
            horizontal, vertical = weighted_position(grey)
            key = '%s.edge.horizontal' % (prefix)
            patch.setvalue(key, horizontal)
            key = '%s.edge.vertical' % (prefix)
            patch.setvalue(key, 1-vertical)

        ####################################################################
        # the following section implements the processing of the flow

        if metrics_flow:
            # crop the image with the optical flow, it is already grey
            flow_horizontal = flow[top:bottom, left:right, 0]
            flow_vertical   = flow[top:bottom, left:right, 1]

            horizontal = np.mean(flow_horizontal, axis=(0,1), dtype=np.float, keepdims=False)
            vertical = np.mean(flow_vertical, axis=(0,1), dtype=np.float, keepdims=False)

            scale = 10/np.sqrt(pixels)
            offset = 0.5

            horizontal = horizontal * scale + offset
            vertical = vertical * scale + offset

            key = '%s.flow.horizontal' % (prefix)
            patch.setvalue(key, horizontal)
            key = '%s.flow.vertical' % (prefix)
            patch.setvalue(key, 1-vertical)


    # remember the frame for the next iteration
    previous = frame
    previous_grey = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)

    if not device==None:
        key = cv2.waitKey(1)
    else:
        key = cv2.waitKey(int(1000./fps))

    if key == ord('q'):
        raise(KeyboardInterrupt)
    elif key == ord('1'):
        show = 'color'
    elif key == ord('2'):
        show = 'grey'
    elif key == ord('3'):
        show = 'diff'
    elif key == ord('4'):
        show = 'edge'
    elif key == ord('5'):
        show = 'flow'


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

    try:
        cap.release()
        cv2.destroyAllWindows()
    except:
        pass
    monitor.success('stopped OpenCV processing')


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
