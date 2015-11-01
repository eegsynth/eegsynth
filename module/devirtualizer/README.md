Devirtualizer module
====================

The goal of this module is to read control values from the REDIS buffer and writes a serial output command to one of the the USB cv/gate converter.


** Requirements **

The REDIS buffer should be running. The control values do not have to exist at the start of execution, as there is an initial default value.


** Software Requirements **

python 2.x
redis python library
ch340 driver (for OS X)
