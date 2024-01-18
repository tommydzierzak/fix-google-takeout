# need to update readme
# folders with an emoji will not work correctly

import sys
import re
import os
import json
import warnings
import argparse
import imghdr  # "Deprecated since version 3.11, will be removed in version 3.13"
from datetime import datetime
import subprocess

from packaging import version
from dateutil.parser import parse
from exiftool import ExifToolHelper

minExiftoolVersion = "12.15"

acceptableFiletypes = (".jpg", ".jpeg", ".png")

logfile = [None]

failedFiles = []


def lprint(s):
    print(s)
    logfile[0].write(s + "\n")


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


def update_datetime(args, fpath):
    existingData = getPhotoTags(fpath)
    if "EXIF:DateTimeOriginal" in existingData:  # Probably a simpler way to handle this chunk of if statements
        if "EXIF:OffsetTimeOriginal" in existingData:  # Check if offset dat exists before printing it
            print(f"File: {fpath}: Has existing date info, keeping at: {existingData['EXIF:DateTimeOriginal']} {existingData['EXIF:OffsetTimeOriginal']}")
        else:  # if not only print the date info
            print(f"File: {fpath}: Has existing date info, keeping at: {existingData['EXIF:DateTimeOriginal']}")
    elif "XMP:DateCreated" in existingData:
        print(f"File: {fpath}: Has existing date info, keeping at: {existingData['XMP:DateCreated']}")
    else:
        new_datetime = get_new_datetime(fpath)
        if new_datetime is None:
            print(f'File: {fpath}: Has no existing date info, and has no matching .json file in this directory... skipping')
            failedFiles.append(fpath)
        else:
            formattedNewDate = new_datetime.strftime("%Y:%m:%d %H:%M:%S")
            if args.showOnly:  # If -s flag is set only print files, don't make any changes
                print(f'File: {fpath}: Has no existing date info, could change to {formattedNewDate}')
            else:  # If -s flag is not set, make changes to files
                print(f'File: {fpath}: Has no existing date info, changing to {formattedNewDate}')
                setPhotoTags(args, formattedNewDate)


def recursively_operate(args):
    if args.recursive:  # If recursive flag is set, use os.walk to iterate directory
        for root, dirs, files in os.walk(args.target):
            for name in files:
                if name.lower().endswith(acceptableFiletypes):
                    try:
                        update_datetime(args, os.path.join(root, name))
                    except Exception as e:
                        lprint("Could not operate %s: %s" % (name, str(e)))
    else:
        for entry in os.scandir(args.target):  # If recursive flag is not set, use os.scandir to iterate directory
            if entry.name.lower().endswith(acceptableFiletypes):
                try:
                    update_datetime(args, entry.path)
                except Exception as e:
                    lprint("Could not operate %s: %s" % (entry.path, str(e)))


def getPhotoTags(file):
    with ExifToolHelper() as et:
        for d in et.get_tags([file], tags=["DateTimeOriginal", "OffsetTimeOriginal", "XMP:DateCreated"]):
            pass
    return d


def setPhotoTags(args, date):
    if args.originals:  # If -o flag is set, keep exiftool defaults and create copies of original files
        exifToolParams = []
    else:  # If -o flag is not set, overwrite original files
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


def versionCheck():
    try:
        result = subprocess.run(['exiftool', '-ver'], stdout=subprocess.PIPE)
    except:
        print("ExifTool does not seem to be installed correctly, please follow the ExifTool install instructions again")
    else:
        if result.returncode == 0:
            exiftoolVersion = '.'.join(re.findall('\d+', str(result.stdout)))
            if version.parse(exiftoolVersion) >= version.parse(minExiftoolVersion):
                print("ExifTool version looks good")
            else:
                print(f"This tool requires ExifTool version {minExiftoolVersion} or higher, it seems you have version {exiftoolVersion}")


def process(args):
    if args.check:
        versionCheck()
    elif args.target == []:
        print("No file or directory target provided")
    else:
        if os.path.isdir(args.target):
            recursively_operate(args)
            return
        if os.path.isfile(args.target):
            if args.recursive:
                warnings.warn("You included the recursive flag but are included the path to a file, not a directory. Ignoring recursive flag.")
            if not args.target.lower().endswith(acceptableFiletypes):
                warnings.warn("only works for JPGs & PNGs")
                return
            else:
                update_datetime(args, args.target)
            return
        print("target is neither file nor directory")


def main():
    parser = argparse.ArgumentParser(prog="fix-google-takeout", description="Fix DateTimeOriginal EXIF tag for Google Takeout images based on data in colocated json files")
    parser.add_argument("target", nargs='?', type=str, default=[], help="file or directory to fix")
    parser.add_argument("-s", "--show", dest="showOnly", action="store_const", const=True, default=False, help="show (don't fix) the current DateTime & available changes")
    parser.add_argument("-r", "--recursive", dest="recursive", action="store_const", const=True, default=False, help="fix all files in all subdirectories")
    parser.add_argument("-o", "--originals", dest="originals", action="store_const", const=True, default=False, help="save an original copy of each edited file")
    parser.add_argument("-c", "--check", dest="check", action="store_const", const=True, default=False, help="check Exiftool version is correct")

    args = parser.parse_args()

    logfile[0] = open("fix-google-takeout.log", "w")

    process(args)

    if failedFiles != []:
        with open('failedFiles.txt', 'w') as outfile:
            outfile.write('\n'.join(str(i) for i in failedFiles))

    logfile[0].close()


if __name__ == "__main__":
    main()
