"""
tests for ratt.py

"""

import os
import sys
import time
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from functools import partial

import py.test

from ratt import processInputArgs
from ratt import getDateTimeString
from ratt import getFileRenameData
from ratt import renameAccordingToTimeAndDate
from ratt import DAYS_OF_WEEK



def test_processInputArgs():
    inp = ""
    confirmation, hourOffset = processInputArgs(inp.split())
    assert confirmation == False
    assert hourOffset == 0

    inp = "-c -o 9"
    confirmation, hourOffset = processInputArgs(inp.split())
    assert confirmation == True
    assert hourOffset == 9

    # wrong offset, should fall back to default
    inp = "-c -o a"
    confirmation, hourOffset = processInputArgs(inp.split())
    assert confirmation == True
    assert hourOffset == 0

    # wrong offset, should fall back to default
    inp = "-c -o 2.3"
    confirmation, hourOffset = processInputArgs(inp.split())
    assert confirmation == True
    assert hourOffset == 0


def test_getDateTimeString():
    d = datetime(2011, 02, 03, 04, 05, 06)
    ts = time.mktime(d.timetuple())
    dow = DAYS_OF_WEEK[d.weekday()]
    s = getDateTimeString(ts, 0)
    assert s == "2011-02-03-%s-04-05-06" % dow

    d = datetime(2011, 02, 03, 01, 05, 06)
    ts = time.mktime(d.timetuple())
    dow = DAYS_OF_WEEK[d.weekday()]
    s = getDateTimeString(ts, 3) # hour offset
    assert s == "2011-02-03-%s-04-05-06" % dow

    # negative offset over midnight, to the previous day
    d = datetime(2011, 02, 03, 01, 05, 06)
    ts = time.mktime(d.timetuple())
    s = getDateTimeString(ts, -3) # hour offset
    # it will also be previous week day now
    dow = DAYS_OF_WEEK[d.weekday() - 1]
    assert s == "2011-02-02-%s-22-05-06" % dow

    # positive offset over midnight
    d = datetime(2011, 02, 03, 20, 05, 06)
    ts = time.mktime(d.timetuple())
    s = getDateTimeString(ts, 9) # hour offset
    # it will also be next week day now
    dow = DAYS_OF_WEEK[d.weekday() + 1]
    assert s == "2011-02-04-%s-05-05-06" % dow


def getFilesNames(fileList):
    names = []
    for f in fileList:
        yield f.name


def getFiles(numFiles):
    # create temporary files to feed names into the tested func.
    files = []
    for i in range(numFiles):
        f = NamedTemporaryFile()
        files.append(f)
    return files


def test_getFileRenameData():
    def doTest(timestamp, inputFiles):
        dataSourceFunc = partial(getFilesNames, inputFiles)
        data = getFileRenameData(dataSourceFunc, 0)
        s = getDateTimeString(timestamp, 0)
        for dateTimeFileName, oldFiles in data.items():
            assert s == dateTimeFileName
            for oldFile1, oldFile2 in zip(oldFiles, getFilesNames(inputFiles)):
                assert oldFile1 == oldFile2
    
    files = getFiles(1)
    # assume the file(s) created within the 'now' second
    now = time.time()
    doTest(now, files)

    files = getFiles(5)
    # assume the file(s) created within the 'now' second
    now = time.time()
    doTest(now, files)


def test_renameAccordingToTimeAndDate():
    """
    This should exercise both conditions where there is only 1 file
    corresponding to a second-time-precision timestamp as well as then
    there is more.

    """
    files = getFiles(1)
    now = time.time()
    dataSourceFunc = partial(getFilesNames, files)
    data = getFileRenameData(dataSourceFunc, 0)
    # tempfile would fail on attemp to rename, don't perform actual rename
    renameAccordingToTimeAndDate(data, False)

    files = getFiles(5)
    now = time.time()
    dataSourceFunc = partial(getFilesNames, files)
    data = getFileRenameData(dataSourceFunc, 0)
    # tempfile would fail on attemp to rename, don't perform actual rename
    renameAccordingToTimeAndDate(data, False)
