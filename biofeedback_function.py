# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 11:06:14 2019

@author: John Doe
"""

import math
import matplotlib.pyplot as plt

min_br = 6
max_br = 30
min_feedback = 0
max_feedback = 1

def mappingfun(x):

#    y = ((x - min_br) * ((max_feedback - min_feedback) / (max_br - min_br)) +
#         min_feedback)
    return 1 / (1 + math.exp(-0.5*(x-15)))#y**2


brs = range(60)
feedback = []

for current_br in brs:

    if current_br <= min_br:
        feedback.append(min_feedback)
    elif current_br >= max_br:
        feedback.append(max_feedback)
    else:
        feedback.append(mappingfun(current_br))
    
    
plt.figure()
ax1 = plt.subplot(211)
ax2 = plt.subplot(212, sharex=ax1)
ax1.plot(feedback, c='r')
ax2.plot(brs)
ax2.axhline(6)

