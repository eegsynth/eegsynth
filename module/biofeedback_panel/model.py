#!/usr/bin/env python3

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
from pyqtgraph import LinearRegionItem, InfiniteLine


class Model(QObject):
    
    # Costum signals.
    psd_changed = pyqtSignal(object)
    biofeedback_changed = pyqtSignal(object)
    breathing_changed = pyqtSignal(object)

    # The following model attributes are set by the controller.
    ###########################################################
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        self.breathing_changed.emit(value)
        
    @property
    def sfreq(self):
        return self._sfreq
    
    @sfreq.setter
    def sfreq(self, value):
        self._sfreq = value
        
    @property
    def psd(self):
        return self._psd
    
    @psd.setter
    def psd(self, value):
        self._psd = value
        self.psd_changed.emit(value)
    
    @property
    def freqs(self):
        return self._freqs
    
    @freqs.setter
    def freqs(self, value):
        self._freqs = value
        
    @property
    def rewardratio(self):
        return self._rewardratio
    
    @rewardratio.setter
    def rewardratio(self, value):
        self._rewardratio = value
        
    @property
    def biofeedback(self):
        return self._biofeedback
    
    @biofeedback.setter
    def biofeedback(self, value):
        self._biofeedback = value
        # Emit both the x-coordinate (rewardratio) and y-coordinate
        # (biofeedback) for the view's biofeedback plot.
        self.biofeedback_changed.emit([self._rewardratio, value])
        
    # The following model attributes are set directly by the view.
    ##############################################################    
       
    @pyqtProperty(object)
    def biofeedbacktarget(self):
        return self._biofeedbacktarget
    
    @pyqtSlot(object)
    def set_biofeedbacktarget(self, value):
        if isinstance(value, type(InfiniteLine())):
            self._biofeedbacktarget = value.value()
        
    @pyqtProperty(str)
    def biofeedbackmapping(self):
        return self._biofeedbackmapping
    
    @pyqtSlot(str)
    def set_biofeedbackmapping(self, value):
        self._biofeedbackmapping = value
        
    @pyqtProperty(object)
    def lowreward(self):
        return self._lowreward
    
    @pyqtSlot(object)
    def set_lowreward(self, value):
        if isinstance(value, type(LinearRegionItem())):
            value = value.getRegion()[0]
            if value != self._lowreward:
                self._lowreward = value
        
    @pyqtProperty(object)
    def upreward(self):
        return self._upreward
    
    @pyqtSlot(object)
    def set_upreward(self, value):
        if isinstance(value, type(LinearRegionItem())):
            value = value.getRegion()[1]
            if value != self._upreward:
                self._upreward = value
        elif isinstance(value, str):
            value = float(value)
            self._upreward = value
        
    @pyqtProperty(object)
    def lowtotal(self):
        return self._lowtotal
    
    @pyqtSlot(object)
    def set_lowtotal(self, value):
        if isinstance(value, type(LinearRegionItem())):
            value = value.getRegion()[0]
            if value != self._lowtotal:
                self._lowtotal = value
        elif isinstance(value, str):
            value = float(value)
            self._lowtotal = value
        
    @pyqtProperty(object)
    def uptotal(self):
        return self._uptotal
    
    @pyqtSlot(object)
    def set_uptotal(self, value):
        if isinstance(value, type(LinearRegionItem())):
            value = value.getRegion()[1]
            if value != self._uptotal:
                self._uptotal = value
        
    @pyqtProperty(int)
    def window(self):
        return self._window
    
    @pyqtSlot(int)
    def set_window(self, value):
        self._window = value * 10
        
    @pyqtProperty(int)
    def channel(self):
        return self._channel
    
    @pyqtSlot(int)
    def set_channel(self, value):
        self._channel = value
    
    @pyqtProperty(str)
    def fthost(self):
        return self._fthost
    
    @pyqtSlot(str)
    def set_fthost(self, value):
        self._fthost = value
        
    @pyqtProperty(int)
    def ftport(self):
        return self._ftport
    
    @pyqtSlot(int)
    def set_ftport(self, value):
        self._ftport = value
        
        
    def __init__(self):
        
        super().__init__()
        
        self._window = 30
        self._channel = 0
        self._fthost = "localhost"
        self._ftport = 1973
        self._psd = None
        self._freqs = None
        self._biofeedback = 0
        self._biofeedbackmapping = "linear"
        self._biofeedbacktarget = 1.5
        self._rewardratio = 0
        self._lowreward = 0.07
        self._upreward = 0.21
        self._lowtotal = 0
        self._uptotal = 1
        self._data = []
        self._sfreq = 10

        
        
            