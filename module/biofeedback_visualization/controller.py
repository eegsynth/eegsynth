#!/usr/bin/env python

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
        
        self.worstfeedback = self._patch.getfloat('feedback', 'worstfeedback')
        self.bestfeedback = self._patch.getfloat('feedback', 'bestfeedback')
        
        self.worstinput = self._patch.getfloat('input', 'worst')
        self.bestinput = self._patch.getfloat('input', 'best')

    def start_model(self):
        # start is an QThread method
        self._model.running = True
        self._model.run()

    def stop_model(self):
        self._model.running = False
        
    
    def compute_feedback(self, currentinput):
        
#        if currentinput < self.mininput:
#            feedback = self.minfeedback
#        elif currentinput > self.maxinput:
#            feedback = self.maxfeedback
#        else:
#            # use affine transformation to map range of input values to range
#            # of output values
#            feedback = ((currentinput - self.mininput) *
#                        ((self.maxfeedback - self.minfeedback) /
#                         (self.maxinput - self.mininput)) +
#                         self.minfeedback) ** 2
        if currentinput < self.bestinput:
            feedback = self.bestfeedback
        elif currentinput > self.worstinput:
            feedback = self.worstfeedback
        else:
            expo = self.worstfeedback * (self.bestfeedback / self.worstfeedback) ** ((currentinput - self.worstinput) / (self.bestinput - self.worstinput))
            feedback = expo
        print(currentinput, feedback)
        
        self.freshfeedback.emit(feedback)
        # publish feedback
        self._patch.setvalue("feedback", feedback)
