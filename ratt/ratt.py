#!/usr/bin/env python

"""
ratt - Rename Aaccording To Time

Renames files in the current directory according to their creation date/time.
Target file name is specified by the predefined pattern:
TARGET_FILE_NAME_PATTERN (variables names and their number must be preserved).

Should files with duplicate times (precision to seconds) be found, the
target file names are counter suffixed.

File extension is preserved.
The time in the final file names can be changed by hour offset argument.

Use case:
Naming photo files from a digital cammera according to date/time name pattern.
Shooting somewhere in different timezone while forgetting to change time on
the camera - use offsetHour argument.

Usage: --help

Author: Zdenek Maxa

"""

TARGET_FILE_NAME_PATTERN = ("%(year)s-%(month)s-%(day)s-%(dow)s-"
                            "%(hour)s-%(minute)s-%(second)s")
DAYS_OF_WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


import sys
import os
import time
from functools import partial
from optparse import OptionParser
from datetime import datetime
from datetime import timedelta



def processInputArgs(inputArgs):
    parser = OptionParser()
    parser.add_option("-c", "--confirm", action="store_true", dest="confirm",
            default=False, help="Confirmation to eventually rename files.")
    parser.add_option("-o", "--offsetHour", dest="offsetHour", default=0,
            help="Modify time in files names by +/- 1 .. 11 hours.")
    options, args = parser.parse_args(inputArgs)
    # sanitize - offset has to be integer
    try:
        offsetHour = int(options.offsetHour)
    except ValueError:
        print("Wrong offset: '%s', setting back default." %
                options.offsetHour)
        offsetHour = 0
    return options.confirm, offsetHour


def getDateTimeString(timestamp, hourOffset):
    """
    Returns string representing the timestamp time, according to the
    date-time string pattern TARGET_FILE_NAME_PATTERN, 
    shifted by +/- offset if defined (if non-zero).

    """
    dt = datetime.fromtimestamp(timestamp)
    if hourOffset:
        dt += timedelta(hours=hourOffset)
    tt = dt.timetuple()
    fnDict = dict(year="%d" % tt[0],
                  month="%02d" % tt[1],
                  day="%02d" % tt[2],
                  dow="%s" % DAYS_OF_WEEK[tt[6]],
                  hour="%02d" % tt[3],
                  minute="%02d" % tt[4],
                  second="%02d" % tt[5])
    fn = TARGET_FILE_NAME_PATTERN % fnDict
    return fn


def getNewFileNames(currFileNames, hourOffset):
    for currFileName in currFileNames:
        if os.path.isdir(currFileName):
            continue
        # get the file's last modification date
        timestamp = os.path.getmtime(currFileName)
        dateTimeFileName = getDateTimeString(timestamp, hourOffset)
        yield dateTimeFileName, currFileName
        

def doRename(oldName, newName, confirmation):
    print("renaming %s -> %s" % (oldName, newName))
    if os.path.exists(newName):
        print("file '%s' exists, exit.")
        sys.exit(1)
    if confirmation:
        os.rename(oldName, newName)


def getFileRenameData(dataSourceFunc, hourOffset):
    fnItems = getNewFileNames(dataSourceFunc(), hourOffset)
    # key = destination filename (still without counter in case of duplicates)
    # value = [list of old names], number of items determines suffix counter
    data = {}
    for dtFileName, currFileName in fnItems:
        try:
            data[dtFileName].append(currFileName)
        except KeyError:
            data[dtFileName] = [currFileName]
    return data


def renameAccordingToTimeAndDate(data, confirmation):
    for dtFileName, currFileNames in data.items():
        counter = 0
        for currFileName in currFileNames:
            counter += 1
            ext = os.path.splitext(currFileName)[1]
            if (len(currFileNames) > 1):
                newName = "%s-%d%s" % (dtFileName, counter, ext)
            else:
                newName = "%s%s" % (dtFileName, ext)
            doRename(currFileName, newName, confirmation)


def main():
    confirmation, hourOffset = processInputArgs(sys.argv[1:])
    dataSourceFunc = partial(os.listdir, os.getcwd())
    data = getFileRenameData(dataSourceFunc, hourOffset)
    renameAccordingToTimeAndDate(data, confirmation)
    if not confirmation:
         print("\n\nrun with '-c' to really perform files renaming.\n")



if (__name__ == "__main__"):
    main()
