# Tutorial 1: Playback data, and display on monitor

We will start with the following setup wherein we will playback data to the buffer as if it is recorded in real-time. This is convenient, since it will allow you to develop and test your BCI without having to rely on real-time recordings.

![Schematic for Tutorial 1](figures/Tutorial1.png)  
_Boxes depict EEGsynth modules. Orange arrows describe time-series data. Blue arrows describe Redis data_

## Starting the data buffer

The EEGsynth uses the FieldTrip buffer to communicate data between modules. It is the place where raw (or processed) data is stored and updated with new incoming data. For more information on the FieldTrip buffer, check the [FieldTrip documentation](http://www.fieldtriptoolbox.org/development/realtime/buffer).

1. Navigate to the buffer module directory `~/eegsynth/src/module/buffer`
2. Copy the `buffer.ini` to your own patch directory, for example to `~/eegsynth/patches/myfirstpatch`
3. Edit your copy of `buffer.ini` to specify the TCP ports on which you want the buffer server to listen. Note that the defaults are probably fine.
4. Now start up the buffer module, using your own `.ini` file: `python buffer.py -i ~/eegsynth/patches/myfirstpatch/buffer.ini`

## Writing pre-recorded data from a file on disk to the buffer

We will then write some prerecorded data into the buffer as if it was being recorded in real-time:

1. Download some example data in .edf format. For example, from our [data directory on Google Drive](https://drive.google.com/drive/folders/0B10S8PeNnxw1ZnZPbUh0RWk0cjA). Or use the data you recorded in the [recording tutorial](https://braincontrolclub.miraheze.org/wiki/Recording_tutorial "Recording tutorial").
2. Place the .edf file in a directory, e.g., in `~/eegsynth/data`
3. Navigate to the playback module directory `~/eegsynth/src/module/playbacksignal`
4. Copy the `playbacksignal.ini` to your own ini directory, for example to `~/eegsynth/patches/myfirstpatch`
5. Edit your copy of `playbacksignal.ini` to direct the playback module to the right edf data file, e.g., under `[playback]` edit: `file=~/eegsynth/data/testBipolar20170827-0.edf`
6. Edit the two `playbacksignal.ini` options for playback and rewind so that it will play back automatically (and not rewind): `play=1` and `rewind=0`
7. Make note that you can comment out (hide from the module) lines of text by adding a semicolon (;) at the beginning of the line
8. Now start up the playback module, using your own `.ini` file: `python playbacksignal.py -i ~/eegsynth/patches/myfirstpatch/playbacksignal.ini`
9. If all is well, the module will print out the samples that it is 'playing back'. This is that data that is successively entered into the buffer as if was just recorded

## Plotting streaming data in the buffer

If you made it so far the buffer is working. However, we can now also read from the buffer and visualize the data as it comes in, using the plotsignal module. Note you need to be in a graphical environment for this.

1. Navigate to the plotsignal module directory `~/eegsynth/src/module/plotsignal`
2. Copy the `plotsignal.ini` to your own ini directory, for example to `~/eegsynth/patches/myfirstpatch`
3. Edit your copy of `plotsignal.ini` to plot the first two channel, by specifying under `[arguments]` that  `channels=1,2`
4. Now start up the plotsignal module, using your own `.ini` file: `python plotsignal.py -i ~/eegsynth/patches/myfirstpatch/plotsignal.ini`
5. If you see your data scroll by, bravo!

_Continue reading: [Tutorial 2](tutorial2.md)_
