# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

min_br = 5
max_br = 40

def mappingfun(x, min_br, max_br):

    x0 = min_br
    y0 = 1
    x1 = max_br
    y1 = 0.0001

    if x < min_br:
        return 1
    elif x > max_br:
        return 0
    else:
        expo = y0 * (y1 / y0) ** ((x - x0) / (x1 - x0))
        # expo = np.exp(((min_br - 1) -x) * (min_br /(max_br - min_br)))
        return expo


mappingfun = np.frompyfunc(mappingfun, 3, 1)

brs = np.linspace(0, 60, 600)
feedback = []

feedback = mappingfun(brs, min_br, max_br)

fig, ax = plt.subplots()
ax.plot(brs, feedback, c='r')
ax.vlines([min_br, max_br], ymin=0, ymax=1)

