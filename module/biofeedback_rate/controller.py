#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:17:57 2019

@author: pi
"""

#import time
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
        self.maxfeedback = self._patch.getfloat('feedback', 'maxfeedback')
        
        self.mininput = self._patch.getfloat('input', 'min')
        self.maxinput = self._patch.getfloat('input', 'max')

    def start_model(self):
        # start is an QThread method
        self._model.running = True
        self._model.start()
#        self.lasttime = None
#        self.lastinput = None

    def stop_model(self):
        self._model.running = False
        
    
    def compute_feedback(self, currentinput):
        
#        currenttime = time.time()
#        
#        if self.lasttime is None:
#            self.lasttime = currenttime - 1
#        if self.lastinput is None:
#            self.lastinput = currentinput
        
#        
#        dt = currenttime - self.lasttime
#        dinput = currentinput - self.lastinput
#        derivative = dinput / dt
#        
#        dtarget = currentinput - self.target
        
#        if dtarget > 0 and derivative > 0:
        if currentinput < self.mininput:
            feedback = self.minfeedback
        elif currentinput > self.maxinput:
            feedback = self.maxfeedback
        else:
            # use affine transformation to map range of input values to range
            # of output values
            feedback = ((currentinput - self.mininput) *
                        ((self.maxfeedback - self.minfeedback) /
                         (self.maxinput - self.mininput)) +
                         self.minfeedback) ** 2
            
#        self.lasttime = currenttime
#        self.lastinput = currentinput
        
        self.freshfeedback.emit(feedback)
        # publish feedback
        self._patch.setvalue("feedback", feedback)
