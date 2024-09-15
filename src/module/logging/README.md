# Logging Module

This module implements a graphical user-interface (GUI) that shows the log messages that it receives over Redis. It provides an alternative to reading those log messages in the terminal window from which you started the module.

## Usage

To implement remote logging, you add the following to the ini-file for your module of choice

```
[general]
debug=1 ; level of detail
logging=somestring
```

which will then result in all logging messages to be sent to Redis. In the logging module you subsequently can specify

```
[input]
logging=somestring,anotherstring
```

which will pick up the messages that were sent to `somestring` and `anotherstring`.

It is not required to send the log messages to different Redis channels, you can also send all of them to a common channel, such as `logging`.

## Command-line usage

You can also specify the remote logging target on the command line. This is especially handy you have an elaborate patch with many modules.

When using the compiled `eegsynth` executable or the `eegsynth` script that is installed with pip, you specify

```
eegsynth --general-logging=logging module1.ini module2.ini
```

and when using the Python code

```
python eegsynth.py --general-logging=logging module1.ini module2.ini
```

or when starting individual modules

```
python module1.py --general-logging=logging --inifile module1.ini
python module2.py --general-logging=logging --inifile module2.ini
```
