#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:17:57 2019

@author: pi
"""

import time
from PyQt5.QtCore import QObject, pyqtSignal


class Controller(QObject):
    
    '''
    any data transformation is handled by the controller
    '''
    
    freshfeedback = pyqtSignal(float)
    
    def __init__(self, model, patch):
        super().__init__()
        self._patch = patch
        self._model = model
        self._model.freshinput.connect(self.compute_feedback)
        
        # specify minimal occlusion (min scaling) and maximal occlusion (max
        # scaling)
        self.minfeedback = self._patch.getfloat('feedback', 'minfeedback')
        self.maxfeedback = self._patch.getfloat('feedback', 'maxffeedback')
        
        self.mininput= self._patch.getint('input', 'min')
        self.maxinput = self._patch.getint('input', 'max')
        
        self.target = self._patch.getstring('feedback', 'target')
        
        self.lasttime = None
        self.lastinput = None
        
       
    def start_model(self):
        # start is an QThread method
        self._model.running = True
        self._model.start()
        self.lasttime = None
        self.lastinput = None

    def stop_model(self):
        self._model.running = False
        
    
    def compute_feedback(self, currentinput):
        
        currenttime = time.time()
        
        if self.lasttime is None:
            self.lasttime = currenttime
        if self.lastinput is None:
            self.lastinput = currentinput
        
        
        dt = currenttime - self.lasttime
        dinput = currentinput - self.lastinput
        derivative = dinput / dt
        
        dtarget = currentinput - self.target
        
        if derivative > 0 and dtarget > 0:
            # use affine transformation to map range of input values to range
            # of output values
            feedback = ((currentinput - self.mininput) *
                        ((self.maxscaling - self.minscaling) /
                         (self.maxinput - self.mininput)) +
                         self.minscaling) ** 2
        else:
            feedback = self.minfeedback
            
        self.lasttime = currenttime
        self.lastinput = currentinput
        
        self.freshfeedback.emit(feedback)
