# Videoprocessing module

This module does live video processing of the video stream from a webcam. It computes a number of features from the video and writes these as control signals to Redis.

## Extra installation instructions for macOS

This depends on the Open Source Computer Vision Library or [OpenCV](https://opencv.org/).

```
pip install opencv-python
pip install opencv-python-headless
```

In the macOS system preferences "Privacy and Security" section you have to allow Camera access to the Terminal application.
