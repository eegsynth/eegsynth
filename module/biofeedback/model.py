#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:21:05 2019

@author: pi
"""

from PyQt5.QtCore import QThread, pyqtSignal
  

class Model(QThread):
    
    fresh_data = pyqtSignal(object)

    def __init__(self, patch, r):
        super(Model, self).__init__()
        self.patch = patch
        self.redis = r
        self.channel = self.patch.getstring('input', 'channel')
        self.running = False

    def run(self):
        pubsub = self.redis.pubsub()
        # this message triggers the event
        pubsub.subscribe(self.channel)
        while self.running:
            for item in pubsub.listen():
                if not self.running:
                    print('breaking')
                    break
                if item['channel'] == str(self.channel):
                    # emit new data
                    print(float(item['data']))
                    self.fresh_data.emit(float(item['data']))
                    