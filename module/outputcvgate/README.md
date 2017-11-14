# Output CV/Gate Module

The goal of this module is to read control values from the REDIS buffer and writes a serial output command to the Arduino-based USB to CV/Gate converter.

## Requirements

The CV/Gate converter should be connected to USB.
The REDIS buffer should be running.

## Software Requirements

Python 2.x
Redis package for Python
CH340 driver (for OS X)
