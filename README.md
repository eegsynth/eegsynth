# eegsynth-matlab
Converting real-time EEG into sounds and music.

This repository contains the MATLAB code for the rapid application development of http://www.eegsynth.org.

## Platform specific notes for Microsoft Windows
Development is done on a VirtualBox with Windows 7, MATLAB 2012b for 64 bit and MATLAB 2011b for 32 bit.

Precompiled mex file are provided, these are linked to a static version of portmidi. To
use these mex files in MATLAB, you might have to install the Microsoft Visual C++ 2010
Redistributable Package, which is available from [1]. This package contains some
additional system libraries that are used by MSVC 2010.

Compiling the mex files from scratch requires that you have a C/C++ compiler installed. We
have used (and only tested with) Microsoft Visual C++ Express 2010, which is available
from [2]. Compiling 64-bit mex files furthermore requires that you have the Windows
Software Development Kit version 7.1 [3].

[1] https://www.microsoft.com/en-us/download/details.aspx?id=5555  
[2] https://www.visualstudio.com/en-us/downloads  
[3] http://stackoverflow.com/questions/1865069/how-to-compile-a-64-bit-application-using-visual-c-2010-express  

## Platform specific notes for Mac OS X
Development is done on a MacBook Pro with OS X 10.9.5 and MATLAB 2012b.

Compilation of the mex files requires that portmidi [4] is present. To compile portmidi 
you need cmake [5]. It is also possible to install a compiled version of portmidi using 
MacPorts [6] with "sudo port install portmidi".

Furthermore, for compilation you probably need to update the library path settings in
compile\_midi.m

[4] http://portmedia.sourceforge.net/portmidi  
[5] http://www.cmake.org  
[6] https://www.macports.org  

## Platform specific notes for Linux
Compilation on Linux requires the ALSA libraries to be installed.
