# Changes

## Sep 15, 2024

- reorganized the Python code in a src/eegsynth, src/lib and src/modules directory
- switched from setup.py to pyproject.toml, which now also includes the version number
- released 0.8.0 with the automatic publish.yml GitHub action

## Jun 13, 2024

- implemented first patch for Perplexity in Ghent (June 2024)
- fixed gyro channels
- released version 0.7.8

## 28 Jan, 2024

- update from pyqtgraph 0.12 to most recent (0.13.3) version
- do not import Qt objects through pyqtgraph, making an explicit pg.GraphicsLayoutWidge
- workaround for numpy.float64 error in pyqtgraph 0.12, typecast to int
- released version 0.7.7

## Aug 27, 2023

- merged the eegsynth and eegsynth-gui applications and added the --gui option
- removed bitalino from default installation, as its dependency PyBluez won't compile
- released 0.7.6 with the combined graphical user interface

## May 17, 2023

- moved the hardware documentation to its own repository
- removed the non-Python binaries and scripts

## May 14, 2023

- released 0.7.5 with working eegsynth and eegsynth-gui command-line executables

## May 13, 2023

- released 0.7.0 up to 0.7.4 including eegsynth-gui and pepipiaf, logging and plottext modules
- the packaged versions 0.7.0 to 0.7.4 all had some problems with the command-line executables and/or dependencies

## May 10, 2023

- implemented plottext module to track slowly changing control values
- improvements to pepipiaf module

## May 7, 2023

- implemented pepipiaf module

## Apr 30, 2023

- add support for remote logging over Redis/ZeroMQ, used by the logging module
- implemented logging module

## Apr 17, 2023

- implemented general eegsynth-gui application for drag-and-drop
- compiled eegsynth command-line application to stand-alone executable
- compiled eegsynth-gui graphical interface to stand-alone executable

## Mar 21, 2023

- implemented videoprocessing module for live webcam/microscope, and video recordings from disk

## Jan 15, 2023

- implemented alternative to Redis based on ZeroMQ

## Jan 7, 2023

- allow general arguments to be passed on the command-line

## Oct 27, 2022

- released version 0.6.0

## Oct 15, 2022

- implemented audiomixer module

## Oct 9, 2022

- implemented unicorn2ft module

## Jul 4, 2022

- implemented example module

## Jun 12, 2022

- released version 0.5.2

## Jun 6, 2022

- released version 0.5.1
- released version 0.5.0
- implemented buffer module

## Jun 1, 2022

- implemented csp module

## Apr 28, 2022

- implemented delaytrigger module

## Mar 31, 2022

- implemented plottopo module

## Mar 24, 2022

- implemented plotimage module

## Feb 20, 2022

- released version 0.4.2
- implemented brainflow2ft module

## Feb 19, 2022

- released version 0.4.1
- released version 0.4.0

## Feb 17, 2022

- implemented demodulatetone module

## Feb 13, 2022

- implemented modulatetone module

## Aug 14, 2020

- implemented biochill module

## Jul 28, 2020

- implemented polarbelt module

## Apr 11, 2020

- released version 0.3.1

## Apr 4, 2020

- released version 0.3.0

## Mar 26, 2020

- released version 0.2.8

## Mar 23, 2020

- released version 0.2.7

## Mar 8, 2020

- released version 0.2.6

## Feb 16, 2020

- released version 0.2.5
- released version 0.2.4

## Feb 15, 2020

- released version 0.2.3

## Feb 2, 2020

- released version 0.2.2

## Jan 19, 2020

- add debugging to the EEGsynth.monitor object

## Jan 4, 2020

- released version 0.2.1
- released version 0.2.0

## Jan 2, 2020

- released version 0.1.1

## Jan 1, 2020

- released version 0.1.0
- implemented general eegsynth command-line application

## Dec 29, 2019

- implemented outputzeromq module
- implemented outputmqtt module
- implemented inputzeromq module
- implemented inputmqtt module

## Nov 23, 2019

- implemented inputlsl module
- implemented outputlsl module

## Sep 24, 2019

- implemented processtrigger module

## Sep 22, 2019

- implemented generatetrigger module

## Sep 8, 2019

- implemented complexity module

## Sep 1, 2019

- implemented sampler module

## Aug 14, 2019

- implemented videoprocessing module

## Jul 28, 2019

- implemented EEGsynth.monitor object for feedback

## Jul 27, 2019

- implemented compressor module

## Jul 26, 2019

- implemented slewlimiter module

## Jul 25, 2019

- implemented vumeter module

## Jun 30, 2019

- implemented threshold module

## May 14, 2019

- implemented outputdmx module

## Apr 22, 2019

- implemented lsl2ft module

## Apr 4, 2019

- implemented inputcontrol module

## Dec 1, 2018

- implemented historysignal module

## Nov 30, 2018

- implemented outputaudio module
- implemented sonification module

## Nov 25, 2018

- implemented EEGsynth.patch object (not sure about the exact date)

## Nov 21, 2018

- implemented generateclock module
- implemented clockmultiplier module
- implemented clockdivider module

## Nov 20, 2018

- implemented outputmidi module
- implemented plottrigger module

## Nov 18, 2018

- implemented geomixer module

## Nov 15, 2018

- implemented audio2ft module

## Jun 3, 2018

- implemented recordtrigger module
- implemented outputgpio module

## May 17, 2018

- implemented bitalino2ft module

## Mar 12, 2018

- implemented plotspectral module

## Jan 7, 2018

- implemented historycontrol module

## Dec 28, 2017

- implemented recordcontrol module
- implemented playbackcontrol module

## Dec 16, 2017

- implemented recordsignal module
- implemented playbacksignal module

## Nov 20, 2017

- implemented generatecontrol module

## Nov 18, 2017

- implemented plotcontrol module

## Nov 14, 2017

- renamed brain module to spectral
- renamed muscle module to rms module

## Oct 29, 2017

- implemented generatesignal module

## Aug 25, 2017

- implemented plotsignal module

## Aug 5, 2017

- implemented cogito module

## Dec 8, 2016

- implemented outputartnet module

## Dec 5, 2016

- implemented launchpad module

## Mar 30, 2016

- implemented endorphines module

## Mar 24, 2016

- implemented quantizer module

## Mar 23, 2016

- implemented preprocessing module
- implemented postprocessing module

## Mar 21, 2016

- implemented inputmidi module

## Mar 17, 2016

- renamed emg module to rms
- renamed eeg module to brain

## Mar 13, 2016

- implemented accelerometer module

## Mar 7, 2016

- implemented outputcvgate module

## Mar 6, 2016

- implemented volcakeys module
- implemented volcabeats module

## Mar 1, 2016

- implemented inputosc module

## Feb 27, 2016

- implemented outputosc module

## Feb 26, 2016

- implemented volcabass module

## Feb 25, 2016

- implemented emg module
- implemented heartrate module

## Nov 27, 2015

- implemented sequencer module

## Nov 23, 2015

- implemented synthesizer module

## Nov 18, 2015

- implemented keyboard module
- implemented launchcontrol module

## Apr 30, 2015

- renamed the project from brainsynth to eegsynth

## Apr 27, 2015

- started off with some MATLAB code
- initial commit
