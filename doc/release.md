# Package releases

The main location for EEGsynth development is on its [GitHub repository](https://github.com/eegsynth/eegsynth).

Packaged versions of EEGsynth are released on [PyPi](https://pypi.org/project/eegsynth/).

## Creating new releases

This [tutorial](https://packaging.python.org/tutorials/packaging-projects/) explains the packaging and release process.

The following commands publish a new release on PyPi:

```bash
pip install setuptools
pip install setuptools-version-command
pip install twine

git tag x.y.z  # use the correct version number, see below
python setup.py sdist bdist_wheel
twine upload --repository-url https://pypi.org/ dist/*
```

## Version numbering

We use [semantic versioning](https://semver.org) for the releases.
