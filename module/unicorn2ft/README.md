# unicorn2ft module

This module receives data from a Unicorn Black Hybrid wireless EEG system and writes it to the FieldTrip buffer. Other modules, such as `plotsignal`, `preprocessing` and `spectral` can subsequently read the data from the buffer and analyze/convert/process it.

This is a pure Python implementation designed to be platform independent. An alternative to get data from the Unicorn system is to use the `UnicornLSL` application that is provided in the Windows software suite, combined with the EEGsynth `lsl2ft` module.
