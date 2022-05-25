# Installation instructions for Windows

When using [Anaconda](https://www.anaconda.com), you would mostly follow the general installation instructions.

## Redis

For Windows you will need to install the Redis server yourself, using `conda install` like this:

```
conda install -c binstar redis-server # see https://anaconda.org/binstar/redis-server
```

## rt-MIDI

There  is no working conda package for rt-MIDI, so you will need to install it with pip like this:

```
pip install python-rtmidi
```

