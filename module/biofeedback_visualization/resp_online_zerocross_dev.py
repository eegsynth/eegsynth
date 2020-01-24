#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 14:06:43 2019

@author: pi
"""

import numpy as np
import matplotlib.pyplot as plt


def extrema_signal(signal, sfreq, enable_plot=False):

    # initiate plot
    if enable_plot is True:
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)

    # set free parameters
    # the moreoften the window is shifted, the more accurate the placement of
    # extrema
    window_size = int(np.ceil(0.3 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.ceil(0.1 * sfreq)

    # initiate variables
    block = 0
    state = 'wrc'
    maxbr = 100
    micsfact = 0.5
    mdcsfact = 0.1
    ics = np.nan
    dcs = np.nan
    mics = np.int(np.rint((micsfact * 60 / maxbr) * sfreq))
    mdcs = np.int(np.rint((mdcsfact * 60 / maxbr) * sfreq))
    lowtafact = 0.25
    typta = np.nan
    lastrisex = 0
    lastfallx = 0
    troughs = []
    peaks = []
    currentmin = np.inf
    currentmax = -np.inf

    lowthresh = 10
    highthresh = 15
    previous_instrate = highthresh


    # number of inter breath intervals to average
    nibi = 3
    nibi += 1

    # start real-time simulation
    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride,
                               block * stride + window_size,
                               dtype=int)

        dat = signal[block_idcs]

        # plot signal
        if enable_plot is True:
            ax1.plot(block_idcs, dat, c='b')

        # find zero-crossings
        greater = dat > 0
        smaller = dat <= 0

        if state == 'wrc':

            # search for rising crossing
            risex = np.where(np.bitwise_and(greater[1:], smaller[:-1]))[0]

            if risex.size == 0:
                # update current minimum
                if np.min(dat) < currentmin:
                    currentmin = np.min(dat)
                    currentmin_idx = block_idcs[np.argmin(dat)]
                block += 1
                continue

            risex = risex[-1]
            risex_idx = block_idcs[risex]
            ics = risex_idx - lastrisex
            dcs = risex_idx - lastfallx
            if np.logical_and(ics > mics, dcs > mdcs):

                lastrisex = risex_idx
                # update current minimum
                if np.min(dat[:risex]) < currentmin:
                    currentmin = np.min(dat[:risex])
                    currentmin_idx = block_idcs[np.argmin(dat[:risex])]
                # declare the current minimum a valid trough
                troughs.append(currentmin_idx)
                # update current maximum
                currentmax = np.max(dat[risex:])
                currentmax_idx = block_idcs[np.argmax(dat[risex:])]
                # switch state
                state = 'wfc'

                if enable_plot is True:
                    ax1.axvline(risex_idx, ymin=-250, ymax=250, c='g')

            block += 1

        elif state == 'wfc':

            # search for falling crossing
            fallx = np.where(np.bitwise_and(smaller[1:], greater[:-1]))[0]

            if fallx.size == 0:
                # update current maximum
                if np.max(dat) > currentmax:
                    currentmax = np.max(dat)
                    currentmax_idx = block_idcs[np.argmax(dat)]
                block += 1
                continue

            fallx = fallx[-1]
            fallx_idx = block_idcs[fallx]
            ics = fallx_idx - lastfallx
            dcs = fallx_idx - lastrisex
            if np.logical_and(ics > mics, dcs > mdcs):

                lastfallx = fallx_idx
                # update current maximum
                if np.max(dat[:fallx]) > currentmax:
                    currentmax = np.max(dat[:fallx])
                    currentmax_idx = block_idcs[np.argmax(dat[:fallx])]
                # apply a threshold to the tidal amplitude; tidal amplitude
                # is defined as vertical distance of through to peak
                currentta = currentmax - currentmin
                if np.isnan(typta):
                    typta = currentta
                typta = (typta + (currentta - typta) / (block + 1))
                lowta = typta * lowtafact
                # if enable_plot is True:
                    # ax2.plot(block_idcs, np.ones(window_size) * currentta, c='g')
                    # ax2.plot(block_idcs, np.ones(window_size) * typta, c='y')
                    # ax2.plot(block_idcs, np.ones(window_size) * lowta, c='r')
                if currentta > lowta:
                    # declare the current maximum a valid peak
                    peaks.append(currentmax_idx)
                    if len(peaks) > nibi:
                        instrate = 60 * sfreq / np.mean(np.diff(peaks[-nibi:]))
                        ratediff = instrate - previous_instrate
                        previous_instrate = instrate
                        # plt.scatter(currentmax_idx, instrate)

                        if instrate < lowthresh:
                            # positive feedback unless increase
                            if ratediff > 3:
                                feedback = 0
                            else:
                                feedback = 1

                        elif instrate > highthresh:
                            # negative feedback unless increase
                            if ratediff < -2:
                                feedback = 1
                            else:
                                feedback = 0

                        else:
                            # negative feedback for increase
                            if ratediff > 3:
                                feedback = 0
                            # positive feedback for decrease
                            elif ratediff < -2:
                                feedback = 1
                            # neutral feedback for abscence of change
                            else:
                                feedback = 0.5

                        if enable_plot is True:
                            if feedback == 1:
                                color = "g"
                            elif feedback == 0:
                                color = "r"
                            elif feedback == 0.5:
                                color = "y"

                            if ratediff > 3:
                                marker = "^"
                            elif ratediff < -2:
                                marker = "v"
                            else:
                                marker = ">"

                            ax2.scatter(currentmax_idx, instrate, c=color,
                                        marker=marker)

                elif currentta < lowta:
                    # always delete the trough of the current tidal amplitude
                    # pair if the tidal amplitude doesn't make it past the
                    # threshold, otherwise consecutive troughs can occur, i.e.,
                    # alternation of troughs and peaks is broken
                    del troughs[-1]
                # update current minimum
                currentmin = np.min(dat[fallx:])
                currentmin_idx = block_idcs[np.argmin(dat[fallx:])]
                # switch state
                state = 'wrc'

                if enable_plot is True:
                    ax1.axvline(fallx_idx, ymin=-250, ymax=250, c='m')

            block += 1

    if enable_plot is True:
        ax1.axhline(0)
        ax1.scatter(troughs, signal[troughs], c='r', marker='v', s=150)
        ax1.scatter(peaks, signal[peaks], c='r', marker='^', s=150)
        ax2.axhline(lowthresh)
        ax2.axhline(highthresh)
