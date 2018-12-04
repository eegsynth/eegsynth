# Geomixer modules

This module takes one control value as input and outputs N control values. The input control value will be mapped bilinear onto two of the output values, i.e. with the input value x, the outputs are x (like the input itself) and 1-x. All other output channels will be 0.

The relevant action happens when the input value is close to 1, or close to 0 for a set amount of time: the bilinear mapping will then switch to two other output channels. Given N output channels, these form the corners of a regular N-sided geometrical polygon. The input value traverses over the edges of this polygon; every time _only_ activating the outputs for the two corners corresponding to that edge. Whenever it dwells close to a corner of the polygon for a certain amount of time, it will switch over from the current edge to the other edge.

You can imagine a triangle with corners A, B and C (and corresponding output channels). The input value can be mapped on edge AB, activating both output A and B to some extent. If the input value lingers at corner B for some time, it switches over to edge BC. At that moment A is 0 and B is 1, so the switch will not immediately change the output values. After the switch, a change in the input control value will cause it to traverse along the BC edge, where B and C will have some output and A will remain 0.

The output on the N channels is only non-zero for the two channels corresponding to the geometrical edge that the input is mapped onto. Furthermore, the sum of all output channels is always 1. The two output channels that are non-zero change over time, depending on the switching at the corners.
