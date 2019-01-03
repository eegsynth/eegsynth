In contrast to most Brain-Computer-Interfaces (BCIs), the EEGsynth is not intended for visual feedback,
but mainly focuses on the control of sonic feedback. We do support the control of light equipment via
DMX (see [output](output.md)). However, visualization in some cases is important for purposes of development,
such as checking the measurement, calibrating the feedback, and understanding complex interactions.
Furthermore, while sonic feedback is ideal for monitoring changes over times in a moment-by-moment manner, it cannot 
represent the changes over time in the same instant. For these purposes you can use several basic plotting
modules:

* [Plotsignal](../module/plotsignal) Plot raw data 
* [Plotspectral](../module/plotspectral) Plot spectrum of raw data
* [Plotcontrol](../module/plotcontrol) Plot control signals from Redis
* [Plottrigger](../module/plottrigger) Plot pub/sub events from Redis