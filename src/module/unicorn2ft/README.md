# unicorn2ft module

This module receives data from a Unicorn Black Hybrid wireless EEG system and writes it to the FieldTrip buffer. Other modules, such as `plotsignal`, `preprocessing` and `spectral` can subsequently read the data from the buffer and analyze/convert/process it.

The Unicorn device should be paired via the Bluetooth settings.

Prior to connecting, the LED gives short flashes every second. After connecting it blinks on and off in a regular pace. When streaming the LED is constantly on. The Bluetooth protocol is documented in a PDF that is hosted on https://github.com/unicorn-bi/Unicorn-Suite-Hybrid-Black.

If you encounter Bluetooth connection problems on macOS, such as the LED keeps giving short flashes which indicates that it is not connecting, open a terminal and type

    sudo pkill bluetoothd

This module stream 16 channels in total: EEG 1 to 8, Accelerometer X, Y, Z, Gyroscope X, Y, Z, Battery Level and Counter. Please note that the Unicorn Recorder and UnicornLSL application which are part of the Windows suite have a 17th channel with a Validation Indicator.


## Alternatives

This is a pure Python implementation designed to be platform independent. An alternative to get data from the Unicorn system is to use the `UnicornLSL` application that is provided in the Windows software suite, combined with the EEGsynth `lsl2ft` module.
