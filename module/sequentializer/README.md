# Sequentializer modules

This module can be used to map a single control value that is between 0 and 1 sequentially onto multiple output channels. The control value will be mapped bilinear between two neighbouring output channels, i.e. one of the output channels will have the value x, whereas the other has the value 1-x.

Given N output channels, these form the corners of a regular N-sided polygon. The input value traverses over the edges of this polygon. Whenever it dwells close to a corner of the polygon for a certain amount of time, it will switch over from the current edge to the other edge.
