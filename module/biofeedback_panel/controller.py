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
                
        # Set timer for computation of biofeedback (update every 2000 msec).
        self.biofeedback_timer = QTimer()
        self.biofeedback_timer.timeout.connect(self.biofeedback)
        self.biofeedback_timer.start(2000)    # in msec
        
        
    def biofeedback_function(self, x, mapping):
        """
        Parameters
        ----------
        x : float
            Physiological input value.
        mapping : str
            Function mapping the input x to a control variable y. Either
            "linear", or "exponential".
        Returns
        -------
        y : float
            Biofeedback control variable in the range [0, 1].
        """
        
        x0 = 0.00001
        x1 = self._model.biofeedbacktarget
        y0 = 0.00001
        y1 = 1
        
        if x >= x1:
            return y1
        
        if mapping == "linear":
            y = y0 + (x - x0) * ((y1 - y0) / (x1 - x0))
            
        elif mapping == "exponential":
            y = y0 * (y1 / y0) ** ((x - x0) / (x1 - x0))
        
        return y
        
    # Compute current breathing estimate (spectral ratio) and derive
    # biofeedback.
    def biofeedback(self):
        # All variables that can be changed dynamically are obtained from the
        # model (i.e., attributes).
        
        header = self._model.ftc.getHeader()
        current_idx = header.nSamples
        sfreq = header.fSample
        sfreq_downsamp = 2
        downsampfact = int(sfreq / sfreq_downsamp)
        if downsampfact <= 1:
            raise RuntimeError(f"Sampling frequency {sfreq} is too low.")
        window_downsamp = int(np.rint(self._model.window * sfreq_downsamp))
        freqs = rfftfreq(window_downsamp, 1 / sfreq_downsamp)
        interpres = 0.025
        freqsintp = np.arange(freqs[0], freqs[-1], interpres)
        self._model.freqs = freqsintp
        rewardrange = np.logical_and(freqsintp >= self._model.lowreward,
                                     freqsintp <= self._model.upreward)
        totalrange = np.logical_and(freqsintp >= self._model.lowtotal,
                                    freqsintp <= self._model.uptotal)
        
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
        
        # Compute biofeedback based on the PSD
        rewardpsd = np.sum(psdintp[rewardrange])
        totalpsd = np.sum(psdintp[totalrange])
        rewardratio = rewardpsd / (totalpsd - rewardpsd)
        self._model.rewardratio = rewardratio
        biofeedback = self.biofeedback_function(rewardratio,
                                                self._model.biofeedbackmapping)
        self._model.biofeedback = biofeedback
        