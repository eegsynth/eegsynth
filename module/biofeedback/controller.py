#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:17:57 2019

@author: pi
"""

from PyQt5.QtCore import QObject, pyqtSignal


class Controller(QObject):
    
    '''
    any data transformation is handled by the controller
    '''
    
    feedback = pyqtSignal(float)
    
    def __init__(self, model, patch):
        super().__init__()
        self._model = model
        self._model.fresh_data.connect(self.feedback_scaling)
        self._patch = patch
        
        # specify minimal occlusion (min scaling) and maximal occlusion (max
        # scaling)
        self.min_scaling = self._patch.getfloat('scaling', 'minscal')
        self.max_scaling = self._patch.getfloat('scaling', 'maxscal')
        
        self.min_input= self._patch.getint('input', 'min')
        self.max_input = self._patch.getint('input', 'max')
       
    def start_model(self):
        self._model.start()
    
    def stop_model(self):
        self._model.stop()
    
    def feedback_scaling(self, data):
        # use affine transformation to map range of input values to range of
        # output values
        scaling = ((data - self.min_input) * 
                   ((self.max_scaling - self.min_scaling) / 
                    (self.max_input - self.min_input)) + 
                    self.min_scaling)
        self.feedback.emit(scaling)
        # also publish feedback
