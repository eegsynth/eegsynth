#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:21:05 2019

@author: pi
"""

from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
        
# use bitalino as parent-/ base-class and inherit it's methods in the model
# child-/subclass
class Model(QObject):
    
    '''
    handles connection to the datasource and serves data to controller
    '''
    
    fresh_data = pyqtSignal(object)

    def __init__(self, patch):
        super().__init__()
        self._patch = patch

#        # simulated data
#        self.fs = 4
#        f = 0.1
#        self.nsamples = 10000
#        self.min_hr = 60
#        self.max_hr = 100
#        x = np.arange(self.nsamples)
#        amp = 0.5 * (self.max_hr - self.min_hr)
#        offset = amp + self.min_hr
#        self.y = amp * np.sin(2 * np.pi * f * x / self.fs) + offset
#        self.currentsamp = 0

        self.min_hr = self._patch.getint('hr', 'min')
        self.max_hr = self._patch.getint('hr', 'max')
        
    def read(self):
#        # for testing w/o Bitalino use simulated data
#        data = self.y[self.currentsamp] #random.uniform(60, 100)
#        self.currentsamp += 1
#        if self.currentsamp == self.nsamples:
#            self.currentsamp = 0
#        self.fresh_data.emit(data)
        data = self._patch.getint('hr', 'input')
        self.fresh_data.emit(data)
    