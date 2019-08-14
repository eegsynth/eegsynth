#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:21:05 2019

@author: pi
"""

from PyQt5.QtCore import QObject, pyqtSignal
from bitalino import BITalino
import numpy as np
        
# use bitalino as parent-/ base-class and inherit it's methods in the model
# child-/subclass
class Model(QObject):
    
    '''
    handles connection to the datasource and serves data to controller
    '''
    
    fresh_data = pyqtSignal(object)

    def __init__(self):
        super().__init__()

#        # hardcode variables for now, later these will be set by the GUI
#        self.macaddress = '20:16:12:22:22:26'
#        self.timeout = None
#        self.sfreq = 1000
#        self.chans = [1]
#        self.nsamples = int(np.ceil(0.5 * self.sfreq))
        
#    def connect(self):
#        if self.macaddress:
#            self.connection = BITalino(self.macaddress, self.timeout)
#            
#    def start(self):
#        self.connection.start(self.sfreq, self.chans)
    
        # simulated data
        self.fs = 4
        f = 0.1
        self.nsamples = 10000
        self.min_hr = 60
        self.max_hr = 100
        x = np.arange(self.nsamples)
        amp = 0.5 * (self.max_hr - self.min_hr)
        offset = amp + self.min_hr
        self.y = amp * np.sin(2 * np.pi * f * x / self.fs) + offset
        self.currentsamp = 0
        
    def read(self):
#        data = self.connection.read(self.nsamples)
        # for testing w/o Bitalino use simulated data
        data = self.y[self.currentsamp] #random.uniform(60, 100)
        self.currentsamp += 1
        if self.currentsamp == self.nsamples:
            self.currentsamp = 0
        self.fresh_data.emit(data)
        
#    def stop(self):
#        self.connection.stop()
#        self.connection.close()
        
        
