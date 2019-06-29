# FieldTrip buffer module

This module starts one or multiple FieldTrip buffers. The FieldTrip buffer acts as a network transparent store for one or multiple channels of ExG data, which are all sampled from the same acquisition device with the same sampling rate. The data is represented as a Nchannels*Ntimepoints matrix in a ring buffer. Furthermore, header information with information on the channels and sampling rate is represented.

Other modules, such as `plotsignal`, `preprocessing`, `spectral` and `rms` can be used to visualize and process the data in the FieldTrip buffer.
