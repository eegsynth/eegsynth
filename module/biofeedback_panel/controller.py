#!/usr/bin/env python3

from PyQt5.QtCore import QObject, QRunnable, QThreadPool
from scipy.interpolate import interp1d
from scipy.signal import detrend
import numpy as np
from numpy.fft import rfftfreq
from spectrum import arburg, arma2psd
import time
import FieldTrip
import redis


class Worker(QRunnable):

    def __init__(self, fn, controller, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.kwargs = kwargs
        self.controller = controller

    def run(self):
        self.fn(self.controller, **self.kwargs)


# decorator that runs Controller methods in Worker thread
def threaded(fn):
    def threader(controller, **kwargs):
        worker = Worker(fn, controller, **kwargs)
        controller.threadpool.start(worker)
    return threader


class Controller(QObject):
    
    def __init__(self, model):
        
        super().__init__()

        self._model = model
        
        self.threadpool = QThreadPool()
        
        # Instantiate FieldTrip client (buffer needs to be running locally).
        # Check if the buffer is running.
        try:
            self.ftc = FieldTrip.Client()
            self.ftc.connect(self._model.fthost, self._model.ftport)
        except ConnectionRefusedError:
            raise RuntimeError(f"Make sure that a FieldTrip buffer is running "
                               f"on \"{self._fthost}:{self._ftport}\"")
        # Wait until there is enough data in the buffer (note that this blocks
        # the event loop on purpose).
        hdr = self.ftc.getHeader()
        while hdr is None:
            time.sleep(1)
            print("Waiting for header.")
            hdr = self.ftc.getHeader()
        while hdr.nSamples < hdr.fSample * self._model.window:
            time.sleep(1)
            print("Waiting for sufficient amount of samples.")
            hdr = self.ftc.getHeader()
            
        # Instantiate Redis client (Redis server needs to be running locally).
        try:
            self.redis = redis.StrictRedis(host="localhost",
                                           port=6379, db=0, charset='utf-8',
                                           decode_responses=True)
            self.redis.client_list()
        except redis.ConnectionError:
            raise RuntimeError("cannot connect to Redis server")
            
        # Start the threads.
        self.get_breathing()
        self.compute_biofeedback()
        
                
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
    @threaded
    def compute_biofeedback(self):
        while True:
            time.sleep(2)
            # All variables that can be changed dynamically are obtained from the
            # model (i.e., attributes).
            
            data, sfreq = self._model.data, self._model.sfreq
            nsamp = len(data)
            freqs = rfftfreq(nsamp, 1 / sfreq)
            interpres = 0.025
            freqsintp = np.arange(freqs[0], freqs[-1], interpres)
            rewardrange = np.logical_and(freqsintp >= self._model.lowreward,
                                         freqsintp <= self._model.upreward)
            totalrange = np.logical_and(freqsintp >= self._model.lowtotal,
                                        freqsintp <= self._model.uptotal)
            overlaprange = np.logical_and(rewardrange, totalrange)
        
            # Detrend and taper the signal.
            data = detrend(data)
            data *= np.hanning(nsamp)
        
            # Compute autoregressive coefficients.
            AR, rho, _ = arburg(data, order=12)
            # Use coefficients to compute spectral estimate.
            psd = arma2psd(AR, rho=rho, NFFT=nsamp)
            # Select only positive frequencies.
            psd = np.flip(psd[int(np.rint(nsamp / 2) - 1):])
        
            # Interpolate PSD at desired frequency resolution in order to be able 
            # to set feedback thresholds at intervals smaller than the original 
            # frequency resolution.
            f = interp1d(freqs, psd)
            psdintp = f(freqsintp)
                        
            # Compute biofeedback based on the PSD
            rewardpsd = np.sum(psdintp[rewardrange])
            totalpsd = np.sum(psdintp[totalrange])
            overlappsd = np.sum(psdintp[overlaprange])
            if overlappsd == totalpsd:
                rewardratio = rewardpsd / totalpsd
            else:
                rewardratio = rewardpsd / (totalpsd - overlappsd)
            biofeedback = self.biofeedback_function(rewardratio,
                                                    self._model.biofeedbackmapping)
           
            # Publish the biofeedback value on the Redis channel.
            self.redis.publish("Feedback", biofeedback)
            
            # Set the model attributes.
            (self._model.freqs,
             self._model.psd ,
             self._model.rewardratio,
             self._model.biofeedback) = (freqsintp, psdintp, rewardratio, biofeedback)
        
        
    @threaded
    def get_breathing(self):
        
        # Important: this must be the only place where updates to the window
        # size are considered. Everywhere else window size needs to be
        # inferred from the number of samples in data. Otherwise race
        # conditions occur where the window size is already updated while the
        # data has still the number of elements specified by the previous
        # window size.
        
        while True:
            time.sleep(0.1)
        
            header = self.ftc.getHeader()
            current_idx = header.nSamples
            sfreq = header.fSample
            self._model.sfreq = sfreq
            
            window = self._model.window
        
            # Get the latest data from the buffer.
            beg = current_idx - window * sfreq
            end = current_idx - 1
            
            while np.sign(beg) == -1:
                print(f"Waiting for {end - beg} samples. Currently {current_idx} samples are in the buffer.")
                time.sleep(1)
                header = self.ftc.getHeader()
                current_idx = header.nSamples
                window = self._model.window
                beg = current_idx - window * sfreq
                end = current_idx - 1
            
            data = self.ftc.getData([beg, end])[:, self._model.channel]
        
            self._model.data = data
        