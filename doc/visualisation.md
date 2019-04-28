# Visualisation

In contrast to many Brain-Computer-Interfaces (BCIs), the EEGsynth is not intended for visual feedback, but mainly focuses on the control of sonic feedback. However, we do support the control of light equipment via Art-Net and DMX (see [output](output.md)).

Visualization is in some cases important for development, for checking the signal quality, for calibrating the feedback, and for understanding complex interactions. Furthermore, while sonic feedback is ideal for monitoring changes over times in a moment-by-moment manner, it does not easily reveal changes over longer time windows. For these purposes you can use several basic plotting modules:

- [Plotsignal](../module/plotsignal) to plot raw data
- [Plotspectral](../module/plotspectral) to plot spectrum of raw data
- [Plotcontrol](../module/plotcontrol) to plot control signals from Redis
- [Plottrigger](../module/plottrigger) to plot pub/sub events from Redis

_Why not continue and do the [first tutorial](tutorial1.md)?_
