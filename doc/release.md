# Package releases

The main location for EEGsynth development is on its [GitHub repository](https://github.com/eegsynth/eegsynth).

Packaged versions of EEGsynth are released on [PyPi](https://pypi.org/project/eegsynth/).

## Creating new releases

This [tutorial](https://packaging.python.org/tutorials/packaging-projects/) explains the packaging and release process.

The following commands are used to publish a new release on PyPi:

```bash
pip install setuptools
pip install twine

edit setup.py     # insert the correct version number
git commit -a     # commit the version number change
git tag -a x.y.z  # tag this commit with the correct version number, see below
git push --tags

python setup.py sdist bdist_wheel
twine upload dist/*
```

_Note: I tried both `setuptools-version-command` and `better-setuptools-git-version` to automatically use the git tag for the version number. They did not work consistently and caused incorrect version numbers upon installation._

## Testing the release process

It is possible to test the packaging and distribution process using this:

```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

```bash
pip install --extra-index-url https://test.pypi.org/simple/ eegsynth
```

It is possible to test the `setup.py` file by doing an install from the local repository like this:

```bash
pip install -e .
```

## Creating compiled binaries

Building a stand-alone executable with [pyinstaller](https://pyinstaller.org/) fails with the default environment, but works when `pip nomkl` is used prior to installing all other conda and pip packages.

Building is done on macOS with

    pyinstaller --noconfirm --onefile --console --icon "/Users/roboos/eegsynth/doc/figures/logo-128.ico" --paths "/Users/roboos/eegsynth/lib" --additional-hooks-dir . "/Users/roboos/eegsynth/eegsynth.py"

     pyinstaller --noconfirm --windowed --icon "/Users/roboos/eegsynth/doc/figures/logo-128.ico" --paths "/Users/roboos/eegsynth/lib" --additional-hooks-dir . "/Users/roboos/eegsynth/eegsynth-gui.py"

or on Windows with

    pyinstaller --noconfirm --onefile --console --icon "C:\Users\robert\Documents\GitHub\eegsynth\doc\figures\logo-128.ico" --paths "C:\Users\robert\Documents\GitHub\eegsynth\lib" --additional-hooks-dir . "C:\Users\robert\Documents\GitHub\eegsynth\eegsynth.py"

    pyinstaller --noconfirm --onefile --windowed --icon "C:\Users\robert\Documents\GitHub\eegsynth\doc\figures\logo-128.ico" --paths "C:\Users\robert\Documents\GitHub\eegsynth\lib" --additional-hooks-dir . "C:\Users\robert\Documents\GitHub\eegsynth\eegsynth-gui.py"

## Version numbering

We use [semantic versioning](https://semver.org) for the releases.
