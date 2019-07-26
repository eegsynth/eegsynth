# Slew Limiter Module

The purpose of this module is to limit how fast control values from Redis can change. This can be used to smooth an otherwise rapidly changing noisy signal, e.g. for the [vumeter](../vumeter) module, or to implement portamento. 
