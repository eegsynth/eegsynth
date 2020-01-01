#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# The organization of the python code is non-standard, hence a custom
# package_dir and packages specification is needed.

setuptools.setup(
    name="eegsynth",
    version="0.0.1",
    author="Robert Oostenveld",
    author_email="r.oostenveld@gmail.com",
    license="GPLv3",
    description="Converting real-time EEG into sounds, music and visual effects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://www.eegsynth.org",
    package_dir={'eegsynth': '.', 'eegsynth.lib': 'lib', 'eegsynth.module': 'module'},
    packages=['eegsynth'] + ['eegsynth.' + s for s in setuptools.find_packages('.')],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires='>=2.7',
)