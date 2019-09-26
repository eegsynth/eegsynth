breathrate module

reads a filtered respiration channel from the FieldTrip buffer (bandpass filtered at 0.05 to 0.5 Hz) and provides an estimate of breathing rate, based on inhalation peaks; peaks are chosen over troughs since the former are more sharply defined than troughs in signals acquired with the [Bitalino belt](https://plux.info/assembled-sensors/40-respiration-pzt-sensor.html);
online averages are update according to [D. Knuth](https://dsp.stackexchange.com/questions/811/determining-the-mean-and-standard-deviation-in-real-time). \
publishes a continuous value that contains the breathing rate in breath per minute `breathrate` channel 
