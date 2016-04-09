#!/usr/bin/env python

import mido
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import redis
import threading
import time
import sys
import os

# the settings dialog distinguishes three colors for sliders/knobs, buttons and switches
slider_name = ['mixer/mixer1_mode', 'mixer/mixer1_fader', 'mixer/mixer2_mode', 'mixer/mixer2_fader', 'mixer/fade_to_black', 'color_fx/saturation', 'color_fx/hue1', 'color_fx/black1', 'color_fx/hue2', 'color_fx/black2', 'transform_fx/tile_mode', 'transform_fx/rotate', 'transform_fx/zoom', 'transform_fx/move_x', 'transform_fx/move_y', 'transform_fx/center_x', 'transform_fx/center_y', 'transform_fx/skew_x', 'transform_fx/skew_y', 'freeframe_fx1/pad1_x', 'freeframe_fx1/pad1_y', 'freeframe_fx1/pad2_x', 'freeframe_fx1/pad2_y', 'freeframe_fx1/pad3_x', 'freeframe_fx1/pad4_y', 'freeframe_fx2/pad1_x', 'freeframe_fx2/pad1_y', 'freeframe_fx2/pad2_x', 'freeframe_fx2/pad2_y', 'freeframe_fx2/pad3_x', 'freeframe_fx2/pad4_y', 'channelA/playback_speed', 'channelA/scrub_timeline', 'channelB/playback_speed', 'channelB/scrub_timeline', 'channelC/playback_speed', 'channelC/scrub_timeline']
slider_code = [31, 32, 33, 34, 35, 45, 0, 0, 0, 0, 0, 53, 54, 56, 55, 58, 57, 60, 59, 69, 68, 71, 70, 73, 72, 82, 81, 84, 83, 86, 85, 3, 10, 14, 20, 24, 30]
button_name = ['color_fx/reset', 'color_fx/channelA', 'color_fx/channelB', 'color_fx/channelC', 'color_fx/channel_master', 'color_fx/black_white', 'color_fx/invert', 'transform_fx/reset', 'transform_fx/channelA', 'transform_fx/channelB', 'transform_fx/channelC', 'transform_fx/channel_master', 'freeframe_fx1/reset', 'freeframe_fx1/channelA', 'freeframe_fx1/channelB', 'freeframe_fx1/channelC', 'freeframe_fx1/channel_master', 'freeframe_fx2/reset', 'freeframe_fx2/channelA', 'freeframe_fx2/channelB', 'freeframe_fx2/channelC', 'freeframe_fx2/channel_master', 'channelA/rewind', 'channelA/previous_loop', 'channelA/next_loop', 'channelA/random_loop', 'channelA/random_timeline', 'channelA/loop_mode', 'channelA/loop1', 'channelA/loop2', 'channelA/loop3', 'channelA/loop4', 'channelA/loop5', 'channelA/loop6', 'channelA/loop7', 'channelA/loop8', 'channelA/loop9', 'channelA/loop10', 'channelA/loop11', 'channelA/loop12', 'channelA/loop13', 'channelA/loop14', 'channelA/loop15', 'channelA/loop16', 'channelA/loop17', 'channelA/loop18', 'channelA/loop19', 'channelA/loop20', 'channelA/loop21', 'channelA/loop22', 'channelA/loop23', 'channelA/loop24', 'channelA/loop25', 'channelA/loop26', 'channelA/loop27', 'channelA/loop28', 'channelA/loop29', 'channelA/loop30', 'channelB/rewind', 'channelB/previous_loop', 'channelB/next_loop', 'channelB/random_loop', 'channelB/random_timeline', 'channelB/loop_mode', 'channelB/loop1', 'channelB/loop2', 'channelB/loop3', 'channelB/loop4', 'channelB/loop5', 'channelB/loop6', 'channelB/loop7', 'channelB/loop8', 'channelB/loop9', 'channelB/loop10', 'channelB/loop11', 'channelB/loop12', 'channelB/loop13', 'channelB/loop14', 'channelB/loop15', 'channelB/loop16', 'channelB/loop17', 'channelB/loop18', 'channelB/loop19', 'channelB/loop20', 'channelB/loop21', 'channelB/loop22', 'channelB/loop23', 'channelB/loop24', 'channelB/loop25', 'channelB/loop26', 'channelB/loop27', 'channelB/loop28', 'channelB/loop29', 'channelB/loop30', 'channelC/rewind', 'channelC/previous_loop', 'channelC/next_loop', 'channelC/random_loop', 'channelC/random_timeline', 'channelC/loop_mode', 'channelC/loop1', 'channelC/loop2', 'channelC/loop3', 'channelC/loop4', 'channelC/loop5', 'channelC/loop6', 'channelC/loop7', 'channelC/loop8', 'channelC/loop9', 'channelC/loop10', 'channelC/loop11', 'channelC/loop12', 'channelC/loop13', 'channelC/loop14', 'channelC/loop15', 'channelC/loop16', 'channelC/loop17', 'channelC/loop18', 'channelC/loop19', 'channelC/loop20', 'channelC/loop21', 'channelC/loop22', 'channelC/loop23', 'channelC/loop24', 'channelC/loop25', 'channelC/loop26', 'channelC/loop27', 'channelC/loop28', 'channelC/loop29', 'channelC/loop30']
button_code = [40, 36, 37, 38, 39, 42, 43, 50, 46, 47, 48, 49, 65, 61, 62, 63, 64, 78, 74, 75, 76, 77, 4, 1, 2, 8, 9, 0, 6, 12, 18, 24, 5, 11, 17, 23, 4, 10, 16, 22, 3, 9, 15, 21, 2, 8, 14, 20, 1, 7, 13, 19, 0, 0, 0, 0, 0, 0, 15, 11, 12, 13, 19, 0, 29, 36, 42, 48, 30, 35, 41, 47, 28, 34, 40, 46, 27, 33, 39, 45, 26, 32, 38, 44, 25, 31, 37, 43, 0, 0, 0, 0, 0, 0, 25, 21, 22, 23, 29, 0, 54, 60, 66, 72, 53, 59, 65, 71, 52, 58, 64, 70, 51, 57, 63, 69, 50, 56, 62, 68, 49, 55, 61, 67, 0, 0, 0, 0, 0, 0]
switch_name = ['color_fx/on_off', 'color_fx/automation', 'transform_fx/on_off', 'transform_fx/automation', 'freeframe_fx1/on_off', 'freeframe_fx1/automation', 'freeframe_fx2/on_off', 'freeframe_fx2/automation', 'channelA/play_pause', 'channelA/forward_reverse', 'channelB/play_pause', 'channelB/forward_reverse', 'channelC/play_pause', 'channelC/forward_reverse']
switch_code = [41, 44, 51, 52, 66, 67, 79, 80, 5, 6, 16, 17, 26, 27]

if False:
    for name, code in zip(slider_name, slider_code):
        print "slider", name, code
    for name, code in zip(button_name, button_code):
        print "button", name, code
    for name, code in zip(switch_name, switch_code):
        print "switch", name, code

# the list of MIDI commands is the only aspect that is specific to the AVmixer interface
control_name = slider_name
control_code = slider_code
note_name = button_name + switch_name
note_code = button_code + switch_code

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0]!='':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(installed_folder,'../../lib'))
import EEGsynth

config = ConfigParser.ConfigParser()
config.read(os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'))

# this determines how much debugging information gets printed
debug = config.getint('general','debug')

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
    if debug>0:
        print "Connected to redis server"
except redis.ConnectionError:
    print "Error: cannot connect to redis server"
    exit()

midichannel = config.getint('midi', 'channel')-1  # channel 1-16 get mapped to 0-15
outputport = EEGsynth.midiwrapper(config)
outputport.open_output()

# this is to prevent two messages from being sent at the same time
lock = threading.Lock()

class TriggerThread(threading.Thread):
    def __init__(self, redischannel, note):
        threading.Thread.__init__(self)
        self.redischannel = redischannel
        self.note = note
        self.running = True
    def stop(self):
        self.running = False
    def run(self):
        pubsub = r.pubsub()
        pubsub.subscribe('AVMIXER_UNBLOCK')  # this message unblocks the redis listen command
        pubsub.subscribe(self.redischannel)    # this message contains the note
        for item in pubsub.listen():
            if not self.running or not item['type'] is 'message':
                break
            if item['channel']==self.redischannel:
                if debug>1:
                    print item['channel'], "=", item['data']
                msg = mido.Message('note_on', note=self.note, velocity=int(item['data']), channel=midichannel)
                lock.acquire()
                outputport.send(msg)
                lock.release()

# each of the notes that can be played is mapped onto a different trigger
trigger = []
for name, code in zip(note_name, note_code):
    split_name = name.split('/')
    if config.has_option(split_name[0], split_name[1]):
        # start the background thread that deals with this note
        this = TriggerThread(config.get(split_name[0], split_name[1]), code)
        trigger.append(this)
        if debug>1:
            print name, 'OK'
    else:
        if debug>1:
            print name, 'FAILED'

# start the thread for each of the notes
for thread in trigger:
    thread.start()

# control values are only relevant when different from the previous value
previous_val = {}
for name in control_name:
    previous_val[name] = None

try:
    while True:
        time.sleep(config.getfloat('general', 'delay'))

        for name, cmd in zip(control_name, control_code):
            split_name = name.split('/')
            # loop over the control values
            val = EEGsynth.getint(split_name[0], split_name[1], config, r)
            if val is None:
                continue#  it should be skipped when not present in the ini or redis
            if val==previous_val[name]:
                continue # it should be skipped when identical to the previous value
            previous_val[name] = val
            msg = mido.Message('control_change', control=cmd, value=val, channel=midichannel)
            if debug>1:
                print cmd, val, name
            lock.acquire()
            outputport.send(msg)
            lock.release()

except KeyboardInterrupt:
    print "Closing threads"
    for thread in trigger:
        thread.stop()
    r.publish('AVMIXER_UNBLOCK', 1)
    for thread in trigger:
        thread.join()
    sys.exit()
