#!/usr/bin/env python3

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
import FieldTrip
import time


class Model(QObject):
    
    # Costum signals.
    psd_changed = pyqtSignal(object)
    biofeedback_changed = pyqtSignal(object)

    # The following model attributes are set by the controller.
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
    def biofeedback(self):
        return self._biofeedback
    
    @biofeedback.setter
    def biofeedback(self, value):
        self._biofeedback = value
        self.biofeedback_changed.emit(value)
        
    # The following model attributes are set directly by the view.
    @pyqtProperty(int)
    def window(self):
        return self._window
    
    @pyqtSlot(int)
    def set_window(self, value):
        self._window = value
        
    @pyqtProperty(int)
    def channel(self):
        return self._channel
    
    @pyqtSlot(int)
    def set_channel(self, value):
        self._channel = value
    
    @pyqtProperty(str)
    def ft_host(self):
        return self._ft_host
    
    @pyqtSlot(str)
    def set_ft_host(self, value):
        self._ft_host = value
        
    @pyqtProperty(int)
    def ft_port(self):
        return self._ft_port
    
    @pyqtSlot(int)
    def set_ft_port(self, value):
        self._ft_port = value

        
    def __init__(self):
        
        super().__init__()
        
        self._window = 30
        self._channel = 0
        self._ft_host = "localhost"
        self._ft_port = 1972
        self._psd = None
        self._freqs = None
        self._biofeedback = None
        
        # Instantiate FieldTrip client.
        # Check if the buffer is running.
        try:
            self.ftc = FieldTrip.Client()
            self.ftc.connect(self._ft_host, self._ft_port)
        except ConnectionRefusedError:
            raise RuntimeError(f"Make sure that a FieldTrip buffer is running "
                               f"on \"{self._ft_host}:{self._ft_port}\"")
        # Wait until there is enough data in the buffer (note that this blocks
        # the event loop on purpose).
        hdr = self.ftc.getHeader()
        while hdr is None:
            time.sleep(1)
            print("Waiting for header.")
            hdr = self.ftc.getHeader()
        while hdr.nSamples < hdr.fSample * self._window:
            time.sleep(1)
            print("Waiting for sufficient amount of samples.")
            hdr = self.ftc.getHeader()
            
    
