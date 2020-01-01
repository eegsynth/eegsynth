# Package releases

The main location for EEGsynth development is on its [GitHub repository](https://github.com/eegsynth/eegsynth).

Packaged versions of EEGsynth are released on [PyPi](https://pypi.org/project/eegsynth/).

## Creating new releases

This [tutorial](https://packaging.python.org/tutorials/packaging-projects/) explains the packaging and release process.

The following commands are used to publish a new release on PyPi:

```bash
pip install setuptools
pip install twine

edit setup.py  # insert the correct version number
git commit -a  # commit the version number change
git tag x.y.z  # tag this commit with the correct version number, see below

python setup.py sdist bdist_wheel
twine upload --repository-url https://pypi.org/ dist/*
```

_Note: I tried both `setuptools-version-command` and `better-setuptools-git-version` to automatically use the git tag for the version number. They did not work consistently and caused incorrect version numbers upon installation._

## Version numbering

We use [semantic versioning](https://semver.org) for the releases.
