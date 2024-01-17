#need to update readme

import sys
import re
import os
import json
import warnings
import argparse
import imghdr
from datetime import datetime

from dateutil.parser import parse
from exiftool import ExifToolHelper 

acceptableFiletypes = (".jpg", ".jpeg", ".png")

logfile = [None]

failedFiles = []


def lprint(s):
    print(s)
    logfile[0].write(s+"\n")


def get_json_filename(fpath):
    if os.path.exists(fpath + ".json"):
        return fpath + ".json"
    if os.path.exists(fpath + ".JSON"):
        return fpath + ".JSON"
    pre, ext = os.path.splitext(fpath)
    if os.path.exists(pre + ".json"):
        return pre + ".json"
    if os.path.exists(pre + ".JSON"):
        return pre + ".JSON"
    if pre.endswith("-edited"):
        pre = re.sub("-edited$", "", pre)
        return get_json_filename(pre + ext)
    regReturn = re.search(r'\((\d+)\)$', pre)
    if regReturn is not None:
        return get_json_filename(pre.removesuffix(regReturn[0]) + ext + regReturn[0])
    return None


def get_new_datetime(fpath):
    json_fname = get_json_filename(fpath)
    if not json_fname:
        return None
    with open(json_fname) as jf:
        try:
            timestamp = json.load(jf)["photoTakenTime"]["timestamp"]
            return datetime.fromtimestamp(float(timestamp))
        except KeyError:
            return None


    elif "XMP:DateCreated" in existingData:
        print(f"File: {fpath}: Has existing date info, keeping at: {existingData['XMP:DateCreated']}")
    else:
        new_datetime = get_new_datetime(fpath)
        if new_datetime is None:
            print(f'File: {fpath}: Has no existing date info, and has no matching .json file in this directory... skipping')
            failedFiles.append(fpath)
        else:
            formattedNewDate = new_datetime.strftime("%Y:%m:%d %H:%M:%S")
            if args.showOnly: #If -s flag is set only print files, don't make any changes
                print(f'File: {fpath}: Has no existing date info, could change to {formattedNewDate}')
            else: #If -s flag is not set, make changes to files
                print(f'File: {fpath}: Has no existing date info, changing to {formattedNewDate}')
                setPhotoTags(fpath, formattedNewDate)


def recursively_operate(target):
    if args.recursive: # If recursove flag is set, use os.walk to interate directory
        for root, dirs, files in os.walk(target):
            for name in files:
                if name.lower().endswith(acceptableFiletypes):
                    try:
                        update_datetime(path.join(root, name))
                    except Exception as e:
                        lprint("Could not operate %s: %s" % (name, str(e)))
    else:
        for entry in os.scandir(target): # If recursove flag is not set, use os.scandir to interate directory
            if entry.name.lower().endswith(acceptableFiletypes):
                    try:
                        update_datetime(entry.path)
                    except Exception as e:
                        lprint("Could not operate %s: %s" % (entry.path, str(e)))

def getPhotoTags(file):
    with ExifToolHelper() as et:
        for d in et.get_tags([file], tags=["DateTimeOriginal", "OffsetTimeOriginal", "XMP:DateCreated"]):
            pass
    return d

def setPhotoTags(file, date):
    if args.originals: #If -o flag is set, keep exiftool defaults and create copies of original files
        exifToolParams = [ ]
    else: #If -o flag is not set, overwrite original files
        exifToolParams = ["-P", "-overwrite_original"]

    try:
        with ExifToolHelper() as et:
            # now = datetime.strftime(datetime.now(), "%Y:%m:%d %H:%M:%S")
            et.set_tags([args], tags={"DateTimeOriginal": date, "OffsetTimeOriginal": "+00:00"}, params=exifToolParams)
    except Exception as e:  # if changing data fails, check that file type matches extension and retry
        fileExtension = imghdr.what(file)
        name, ext = os.path.splitext(file)

        if ext == ".jpg":
            extHold = "jpeg"
        else:
            extHold = ext.split(".")[1]

        if fileExtension.lower() != extHold.lower():
            newFilename = name + ext.replace(".", "_") + "." + fileExtension
            print(f'the preceding file seems to be a {fileExtension} but is saved as a {extHold}, renaming to:  {newFilename}')
            try:
                os.rename(file, newFilename)
                with ExifToolHelper() as et:
                    # now = datetime.strftime(datetime.now(), "%Y:%m:%d %H:%M:%S")
                    et.set_tags([newFilename], tags={"DateTimeOriginal": date, "OffsetTimeOriginal": "+00:00"}, params=exifToolParams)
            except Exception as e:
                lprint("Could not operate %s: %s" % (entry.path, str(e)))
                failedFiles.append(file)
        else:
            lprint("Could not operate %s" % (file))
            failedFiles.append(file)

    return

def main(target):
    if os.path.isdir(target):
        recursively_operate(target)
        return
    if os.path.isfile(target):
        if args.recursive:
            warnings.warn("You included the recursive flag but are included the path to a file, not a directory. Ignoring recursive flag.")
        if not target.lower().endswith(acceptableFiletypes):
            print("only works for JPGs & PNGs")
            return
        update_datetime(target)
        return
    print("target is neither file nor directory")


parser = argparse.ArgumentParser(
    prog="fix-google-takeout",
    description="Fix DateTimeOriginal EXIF tag for Google Takeout images based on data in colocated json files",
)
parser.add_argument("target", help="file or directory to fix")
parser.add_argument(
    "-s",
    "--show",
    dest="showOnly",
    action="store_const",
    const=True,
    default=False,
    help="show (don't fix) the current DateTime & avaliable changes",
)
parser.add_argument(
    "-r",
    "--recursive",
    dest="recursive",
    action="store_const",
    const=True,
    default=False,
    help="fix all files in all subdirectories",
)
parser.add_argument(
    "-o",
    "--originals",
    dest="originals",
    action="store_const",
    const=True,
    default=False,
    help="save an original copy of each editied file",
)

if __name__ == "__main__":
    args = parser.parse_args()
    logfile[0] = open("fix-google-takeout.log", "w")
    if failedFiles != []:
        with open('failedFiles.txt', 'w') as outfile:
            outfile.write('\n'.join(str(i) for i in failedFiles))
    logfile[0].close()
