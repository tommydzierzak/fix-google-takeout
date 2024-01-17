# fix-google-takeout
- [fix-google-takeout](#fix-google-takeout)
  - [Warning](#warning)
  - [Overview](#overview)
  - [Fork Note](#fork-note)
  - [Current Limitations/ Future Improvements](#current-limitations-future-improvements)
  - [Installation](#installation)
    - [Step 1: Install ExifTool](#step-1-install-exiftool)
      - [Easy method:](#easy-method)
      - [Slightly less easy method:](#slightly-less-easy-method)
    - [Step 2: Clone this repo](#step-2-clone-this-repo)
    - [Step 3: Create and activate virtual environment](#step-3-create-and-activate-virtual-environment)
    - [Step 4: Install requirements](#step-4-install-requirements)
    - [Step 5: Check install](#step-5-check-install)
  - [Execution !! Needs updated !!](#execution--needs-updated-)

## Warning
Use at your own risk. Backup your photos.

## Overview
Google takeout (https://takeout.google.com/settings/takeout) for photos mangles the datetime EXIF data for some reason. The original datetime is available in metadata json sidecar files that accompany the images. This program attempts to use that metadata to fix the datetime in the jpeg or png's EXIF data.

## Fork Note
I forked this repo from [xmonkee/fix-google-takeout](https://github.com/xmonkee/fix-google-takeout), and used it for a majority of my exported Google Photos. However, the python library used in the script ([piexif](https://pypi.org/project/piexif)) does not support PNGs which I had many of in my library. So I rewrote the tool using Phil Harvey's excellent [ExifTool](https://exiftool.org/). Additionally, I added a few other enhancements:
* When changing the EXIF data the tool can optionally add a copy of the pre-changed photo
* The tool can no operate on a single directory, rather than having to recursively operate on all lower directories
* (in progress: add tool to check if python script can access exiftool)

## Current Limitations/ Future Improvements
Directories with names that contain emojis don't seem to work with python's os.path.isdir() & os.path.isfile()

Logfile for changed files & files where new date data could not be found

## Installation

### Step 1: Install ExifTool
#### Easy method:
Use your preferred package manager to install [ExifTool](https://exiftool.org/):

|Mac: [brew](https://brew.sh/)|Windows: [scoop](https://scoop.sh/)|Windows: [choco](https://chocolatey.org/)|Windows: [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)|
|:---:|:---:|:---:|:---:|
|```brew install exiftool```|```scoop install exiftool```|```choco install exiftool```|```winget install exiftool```|

#### Slightly less easy method:
Follow the instructions for your platform on the [ExifTool Website](https://exiftool.org/install.html).

### Step 2: Clone this repo

```
git clone https://github.com/tommydzierzak/fix-google-takeout.git
cd fix-google-takeout
```

### Step 3: Create and activate virtual environment

|Mac:|Windows:|
|:---:|:---:|
|```python -m venv venv``` <br> ```venv\Scripts\activate.bat```|```python -m venv venv``` <br> ```venv\Scripts\activate.bat```|

### Step 4: Install requirements

```
pip install -r requirements.txt
```

### Step 5: Check install

```
!! Add step to check if install is correct !!
```


## Execution !! Needs updated !!
```
./fix-google-takeout -h

usage: fix-google-takeout [-h] [--show] [-r] target

Fix DateTimeOriginal EXIF tag for Google Takeout images based on data in colocated json files

positional arguments:
  target           file or directory to fix

optional arguments:
  -h, --help       show this help message and exit
  --show           show (don't fix) the current DateTime
  -r, --recursive  fix all files in all subdirectories
```
