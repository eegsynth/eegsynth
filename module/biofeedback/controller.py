#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:17:57 2019

@author: pi
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class Controller(QObject):
    
    '''
    any data transformation is handled by the controller
    '''
    
    scaling_update = pyqtSignal(float)
    
    def __init__(self, model, patch):
        super().__init__()
        self._model = model
        self._model.fresh_data.connect(self.map_scaling)
        self._patch = patch
        
        # specify minimal occlusion (min scaling) and maximal occlusion (max
        # scaling)
        self.min_scaling = self._patch.getfloat('scaling', 'minscal')
        self.max_scaling = self._patch.getfloat('scaling', 'maxscal')
        
        
    def start_plotting(self):
        # disable while using random number generator
        # set a timer that fetched new data from the model every 100m sec
        self.timer = QTimer()
        self.timer.timeout.connect(self._model.read)
        timeout = self._patch.getint('general', 'delay')
        self.timer.setInterval(timeout) # timeout in milliseconds
        self.timer.start()
        
    def stop_plotting(self):
        self.timer.stop()
        
    def map_scaling(self, data):
        # use affine transformation to map range of HR values to range of
        # scaling values
        scaling = ((data - self._model.min_hr) * 
                   ((self.max_scaling - self.min_scaling) / 
                    (self._model.max_hr - self._model.min_hr)) + 
                    self.min_scaling)
        self.scaling_update.emit(scaling)




