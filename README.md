---
output:
  pdf_document: 
    highlight: haddock
  html_document:
    css: ~/Dokumente/github.css
    highlight: kate
    theme: journal
---
# ZF Tracker

The **ZF Tracker** is a tool to track the location and
movement of larvae, especially designed for thigmotaxis
experiments. It is intended to work on videos of one fish
per arena.

The output of the tool can range from just the statistics on the
thigmotactic behaviour to the complete list of tracked points and a
visual representation of the path traversed by the fish. Optionally
also temporary results like the segmentation of the video can be saved.

## Requirements

ZF Tracker is a package and script written in Python 3.5. Installing
the Python via the  [Anaconda](https://www.continuum.io/downloads)
python distribution is recommended as contains most required packages.

Additionally the **OpenCV3** package is needed. It can be downloaded and
installed from [conda menpo](https://anaconda.org/menpo/opencv3/).

### External tools

The following external programs are needed for the execution of ZF Tracker:
* [FIJI (ImageJ)](http://imagej.net/Fiji)
* [ffmpeg](https://ffmpeg.org/download.html)

For Windows and Linux it is recommended to add the program to the PATH variable.
For MacOSX users, installing the tools in the Applications folder is recommended.
If you choose to install FIJI or ffmpeg in a different directory or choose
not to add them to PATH, you need to edit the corresponding file in the
**external/data/** folder of the ZF Tracker.

## Installation

Extract the compressed folder to any location on your file system. Build
and install the package by executing the following commands:

```
python setup.py build
python setup.py install
```

## Usage

To use the tracker, first create an empty folder in your file system.
This folder will store all temporary as well as the final results.

The script can be run using the following command line:

```
zf_tracking.py [options] <path/to/video.file> <path/to/result.dir>
```

The following options are allowed:

```
positional arguments:
  in_path               Path to the video.
  out_path              Directory for results. Should be empty.

optional arguments:
  -h, --help            show this help message and exit
  -x, --delete_temp     Delete temporary folder after execution.
  -t, --only_tracking   Only perform tracking step.
  -n NUMBER, --number NUMBER
                        Number of wells to track, default is 24
  -i, --save_track_image
                        Save images of tracked paths.
  -m, --manual_crop     Manually select the wells to be tracked.
  -s, --save_track      Save track points to file.
  --median              Use median intensity projection for segmentation.
  -c CPU, --cpu CPU     Set number of threads for multi core machines.
  --big                 Reduces memory usage for very large video files (time
                        intensive, not recommended).
```

The default configuration of the script is for videos of zebrafish
larvae in 24 well plates. In this case, the user is prompted to
draw a grid over the video, assigning the positions of the wells.
If a different number of wells should be tracked, the wells need to
be assigned manually one by one.

In the subsequent step, the user has to specify the area of the inner
area for the thigmotaxis experiment.

* To assign wells or arena areas, click and drag over the video frame
* To accept the selection, press **c**
* To redo the selection, press **r**

## Troubleshooting

The quality of the tracking depends a lot on the quality of the video.
Make sure, the video is captured in a room without other movement.
Also make sure, that the wells in the videos don't have a lot of
distortion from the perspective.
