# eegsynth-matlab
Converting real-time EEG into sounds and music

## Platform specific notes for Mac OS X
Compilation of the mex files requires that portmidi is present. This can be downloaded
from http://portmedia.sourceforge.net/portmidi. Compilation of portmidi requires cmake.
It is also possible to install a compiled version of portmidi using MacPorts ("sudo port
install portmidi").

Furthermore, for compilation you probably need to update the library path settings in
compile\_midi.m

## Platform specific notes for Microsoft Windows
Precompiled mex file are provided, these are linked to a static version of portmidi.  To
use these mex files in MATLAB, you might have to install the Microsoft Visual C++ 2010
Redistributable Package, which is available from [1]. This package contains some
additional system libraries that are used by MSVC 2010.

[1] https://www.microsoft.com/en-us/download/details.aspx?id=5555

## Platform specific notes for Linux
Compilation on Linux requires the ALSA libraries to be installed.
