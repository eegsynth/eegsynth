#!/usr/bin/env python3

from PyQt5.QtCore import QObject, QTimer
from scipy.signal import decimate, detrend
from scipy.interpolate import interp1d
import numpy as np
from numpy.fft import rfftfreq
from spectrum import arburg, arma2psd



class Controller(QObject):

    def __init__(self, model):
        
        super().__init__()

        self._model = model
                
        # Set timer for computation of PSD (update PSD every 2000 msec)
        self.biofeedback_timer = QTimer()
        self.biofeedback_timer.timeout.connect(self.biofeedback)
        self.biofeedback_timer.start(2000)    # in msec
        

    # Compute current breathing estimate (spectral ratio) and derive
    # biofeedback.
    def biofeedback(self):
        
        header = self._model.ftc.getHeader()
        current_idx = header.nSamples
        sfreq = header.fSample
        sfreq_downsamp = 2
        downsampfact = int(sfreq / sfreq_downsamp)
        window_downsamp = int(np.rint(self._model.window * sfreq_downsamp))
        freqs = rfftfreq(window_downsamp, 1 / sfreq_downsamp)
        interpres = 0.025
        self._model.freqs = np.arange(freqs[0], freqs[-1], interpres)
        
        # Get the latest data from the buffer.
        beg = current_idx - self._model.window * sfreq
        end = current_idx - 1
        data = self._model.ftc.getData([beg, end])[:, self._model.channel]
    
        # Downsample signal (important to use fir not iir).
        data = decimate(data, downsampfact, ftype="fir")
    
        # Detrend and taper the signal.
        data = detrend(data)
        data *= np.hanning(window_downsamp)
    
        # Compute autoregressive coefficients.
        AR, rho, _ = arburg(data, order=12)
        # Use coefficients to compute spectral estimate.
        psd = arma2psd(AR, rho=rho, NFFT=window_downsamp)
        # Select only positive frequencies.
        psd = np.flip(psd[int(np.rint(window_downsamp / 2) - 1):])
    
        # Interpolate PSD at desired frequency resolution in order to be able 
        # to set feedback thresholds at intervals smaller than the original 
        # frequency resolution.
        f = interp1d(freqs, psd)
        psdintp = f(self._model.freqs)
        
        self._model.psd = psdintp
