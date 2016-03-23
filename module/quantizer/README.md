Quantizer module
================

The purpose of this module is to quantize control values from the redis buffer, i.e. round them to the nearest value of a pre-specified list. The output values are subsequently looked up in matching lists, and can be shifted with a certain amount (e.g. octave, fifth) or can represent a non-linear transformation.

## Requirements

The REDIS buffer should be running.

## Software Requirements

Python 2.x
Redis Python library
