"""
tests for ratt.py

TODO:
    exif stuff not tested

"""

import os
import sys
import time
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from functools import partial

import py.test

from ratt import process_input_args
from ratt import get_date_time_string
from ratt import get_file_rename_data
from ratt import rename_according_to_time_and_date
from ratt import DAYS_OF_WEEK


def test_process_input_args():
    inp = ""
    confirmation, hour_offset, exif = process_input_args(inp.split())
    assert confirmation is False
    assert hour_offset == 0
    assert exif is False

    inp = "-c -o 9"
    confirmation, hour_offset, exif = process_input_args(inp.split())
    assert confirmation is True
    assert hour_offset == 9

    # wrong offset, should fall back to default
    inp = "-c -o a"
    confirmation, hour_offset, exif = process_input_args(inp.split())
    assert confirmation is True
    assert hour_offset == 0

    # wrong offset, should fall back to default
    inp = "-c -o 2.3 -e"
    confirmation, hour_offset, exif = process_input_args(inp.split())
    assert confirmation is True
    assert hour_offset == 0
    assert exif is True


def test_get_date_time_string():
    d = datetime(2011, 2, 3, 4, 5, 6)
    ts = time.mktime(d.timetuple())
    dow = DAYS_OF_WEEK[d.weekday()]
    s = get_date_time_string(ts, 0)
    assert s == "2011-02-03-%s-04-05-06" % dow

    d = datetime(2011, 2, 3, 1, 5, 6)
    ts = time.mktime(d.timetuple())
    dow = DAYS_OF_WEEK[d.weekday()]
    s = get_date_time_string(ts, 3)  # hour offset
    assert s == "2011-02-03-%s-04-05-06" % dow

    # negative offset over midnight, to the previous day
    d = datetime(2011, 2, 3, 1, 5, 6)
    ts = time.mktime(d.timetuple())
    s = get_date_time_string(ts, -3)  # hour offset
    # it will also be previous week day now
    dow = DAYS_OF_WEEK[d.weekday() - 1]
    assert s == "2011-02-02-%s-22-05-06" % dow

    # positive offset over midnight
    d = datetime(2011, 2, 3, 20, 5, 6)
    ts = time.mktime(d.timetuple())
    s = get_date_time_string(ts, 9)  # hour offset
    # it will also be next week day now
    dow = DAYS_OF_WEEK[d.weekday() + 1]
    assert s == "2011-02-04-%s-05-05-06" % dow


def get_files_names(file_list):
    names = []
    for f in file_list:
        yield f.name


def get_files(num_files):
    # create temporary files to feed names into the tested func.
    files = []
    for i in range(num_files):
        f = NamedTemporaryFile()
        files.append(f)
    return files


def test_get_file_rename_data():
    def do_test(timestamp, input_files):
        data_source_func = partial(get_files_names, input_files)
        data = get_file_rename_data(data_source_func, 0, False)
        s = get_date_time_string(timestamp, 0)
        for date_time_file_name, old_files in data.items():
            assert s == date_time_file_name
            for old1, old2 in zip(old_files, get_files_names(input_files)):
                assert old1 == old2

    files = get_files(1)
    # assume the file(s) created within the 'now' second
    now = time.time()
    do_test(now, files)

    files = get_files(5)
    # assume the file(s) created within the 'now' second
    now = time.time()
    do_test(now, files)


def test_rename_according_to_time_and_date():
    """
    This should exercise both conditions where there is only 1 file
    corresponding to a second-time-precision timestamp as well as then
    there is more.

    """
    files = get_files(1)
    now = time.time()
    data_source_func = partial(get_files_names, files)
    data = get_file_rename_data(data_source_func, 0, False)
    # tempfile would fail on attemp to rename, don't perform actual rename
    rename_according_to_time_and_date(data, False)

    files = get_files(5)
    now = time.time()
    data_source_func = partial(get_files_names, files)
    data = get_file_rename_data(data_source_func, 0, False)
    # tempfile would fail on attemp to rename, don't perform actual rename
    rename_according_to_time_and_date(data, False)
