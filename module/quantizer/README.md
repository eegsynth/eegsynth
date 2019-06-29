# Quantizer Module

The purpose of this module is to quantize control values from Redis, i.e. round them to the nearest value of a pre-specified list. The output values are subsequently looked up in matching lists. The output value can simply be quantized, can also be shifted with a certain amount (e.g. octave, fifth) or can even represent a non-linear transformation.
