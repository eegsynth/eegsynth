# Heart rate module

This module reads an ECG channel from the FieldTrip buffer and detects heart beats in the ECG signal by thresholding the QRS complex. A trigger message is sent to Redis upon each detected heart beat, and the heart rate is written as a continuous control value to the Redis buffer (expressed in beats per minute).

This module has two outputs: the `heartrate` is a continuous variable that contains the heart rate in BPM. It is updated at every heart beat that is detected. The `heartbeat` also contains the rate in BPM, but it switches back to zero after a short (configurable) duration, which means that it can be used as a gate or as a note that is pressed and released.
