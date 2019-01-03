# Editing and organizing your patches

Each module directory contains an ini file in their respective directory, with a filename identical 
to the module. E.g. [module/spectral](https://github.com/eegsynth/eegsynth/tree/master/module/spectral)
contains [spectral.py](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.py) 
and [spectral.ini](https://github.com/eegsynth/eegsynth/tree/master/module/spectral/spectral.ini). 
This ini file shows the required fields and some default values. However, you should save your 
edited ini files in a separate 'patch directory'. In this patch directory you store all the .ini files 
belonging to one patch. This helps organizing your patches as well as your local git repository, 
which will then not create conflicts with the remote (default) .ini files.
You can find several examples of patch directories in the [patches directory](https://github.com/eegsynth/eegsynth/patches).
These also function as documentation of past performances. 

