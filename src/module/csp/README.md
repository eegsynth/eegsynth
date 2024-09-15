# CSP module

Csp calculates a common spatial pattern from a series of files and outputs
them as Redis values for use as a spatial filter (montage) in preprocessing
Currently only a two-state solution is supported.

The Python implementation of the CSP is a copy of:
https://github.com/spolsley/common-spatial-patterns/blob/master/CSP.py, who
based the algorithm on:

Wang, Yunhua, Patrick Berg, and Michael Scherg. "Common spatial subspace decomposition applied to analysis of brain responses under multiple task conditions: a simulation study." Clinical Neurophysiology 110.4 (1999): 604-614. (available online through Elsevier at https://www.sciencedirect.com/science/article/pii/S138824579800056X)
