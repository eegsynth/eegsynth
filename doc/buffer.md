# Buffer

The EEGsynth uses the FieldTrip buffer to exchange eletrophysiological data between modules. 
It is the place where raw (or processed) data is stored and updated with new incoming data. 
For more information on the FieldTrip buffer, check the [FieldTrip documentation](http://www.fieldtriptoolbox.org/development/realtime/buffer). 
Note that the FieldTtrip buffer allows parallel reading of data. 
Some modules, such as the *spectral* module, take data from the FieldTrip buffer as input, then output 
values to the [Redis buffer](redis.md). 
Other modules take care of data acquisition, interfacing with acquisition devices and updating the 
FieldTrip buffer with incoming data.  
