# Package releases

The main location for EEGsynth development is on its [GitHub repository](https://github.com/eegsynth/eegsynth).

Packaged versions of EEGsynth are released on [PyPi](https://pypi.org/project/eegsynth/).

## Creating new releases

This [tutorial](https://packaging.python.org/tutorials/packaging-projects/) explains the general packaging and release process.

The repository contrains a [publish.yml](https://github.com/eegsynth/eegsynth/blob/master/.github/workflows/publish.yml) action that automatically generates and publishes a new version to [PyPi](https://pypi.org/project/eegsynth/) when a new release is made on GitHub.

## Creating compiled binaries

Building a stand-alone executable with [pyinstaller](https://pyinstaller.org/) fails with the default environment, but works when `conda install nomkl` is used prior to installing all other conda and pip packages.

Building is done on macOS with

    pyinstaller --noconfirm --onefile --console --icon "/Users/roboos/eegsynth/doc/figures/logo-128.ico" --paths "/Users/roboos/eegsynth" --paths "/Users/roboos/eegsynth/lib" "/Users/roboos/eegsynth/bin/eegsynth.py"

     pyinstaller --noconfirm --windowed --icon "/Users/roboos/eegsynth/doc/figures/logo-128.ico" --paths "/Users/roboos/eegsynth" --paths "/Users/roboos/eegsynth/lib" "/Users/roboos/eegsynth/bin/eegsynth-gui.py"

or on Windows with

    pyinstaller --noconfirm --onefile --console --icon "C:\Users\robert\Documents\GitHub\eegsynth\doc\figures\logo-128.ico" --paths "C:\Users\robert\Documents\GitHub\eegsynth" --paths "C:\Users\robert\Documents\GitHub\eegsynth\lib" "C:\Users\robert\Documents\GitHub\eegsynth\eegsynth.py"

    pyinstaller --noconfirm --onefile --windowed --icon "C:\Users\robert\Documents\GitHub\eegsynth\doc\figures\logo-128.ico" --paths "C:\Users\robert\Documents\GitHub\eegsynth" --paths "C:\Users\robert\Documents\GitHub\eegsynth\lib" "C:\Users\robert\Documents\GitHub\eegsynth\eegsynth-gui.py"

## Version numbering

We use [semantic versioning](https://semver.org) for the releases.
