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
the camera - use offset_hour argument.


Usage:
    ratt.py --help


Tests [run from the ratt.py directory]:
    py.test
    py.test --pep8


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


def process_input_args(inputArgs):
    parser = OptionParser()
    parser.add_option("-c", "--confirm", action="store_true", dest="confirm",
                      default=False,
                      help="Confirmation to eventually rename files.")
    parser.add_option("-o", "--offset_hour", dest="offset_hour", default=0,
                      help="Modify time in files names by +/- 1 .. 11 hours.")
    options, args = parser.parse_args(inputArgs)
    # sanitize - offset has to be integer
    try:
        offset_hour = int(options.offset_hour)
    except ValueError:
        print("Wrong offset: '%s', setting back default." %
              options.offset_hour)
        offset_hour = 0
    return options.confirm, offset_hour


def get_date_time_string(timestamp, hour_offset):
    """
    Returns string representing the timestamp time, according to the
    date-time string pattern TARGET_FILE_NAME_PATTERN,
    shifted by +/- offset if defined (if non-zero).

    """
    dt = datetime.fromtimestamp(timestamp)
    if hour_offset:
        dt += timedelta(hours=hour_offset)
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


def get_new_file_names(curr_file_names, hour_offset):
    for name in curr_file_names:
        if os.path.isdir(name):
            continue
        # get the file's last modification date
        timestamp = os.path.getmtime(name)
        date_time_file_name = get_date_time_string(timestamp, hour_offset)
        yield date_time_file_name, name


def do_rename(old_name, new_name, confirmation):
    print("renaming %s -> %s" % (old_name, new_name))
    if os.path.exists(new_name):
        print("file '%s' exists, exit.")
        sys.exit(1)
    if confirmation:
        os.rename(old_name, new_name)


def get_file_rename_data(data_source_func, hour_offset):
    # file name items
    fn_items = get_new_file_names(data_source_func(), hour_offset)
    # key = destination filename (still without counter in case of duplicates)
    # value = [list of old names], number of items determines suffix counter
    data = {}
    # date time file name
    for dt_file_name, curr_file_name in fn_items:
        try:
            data[dt_file_name].append(curr_file_name)
        except KeyError:
            data[dt_file_name] = [curr_file_name]
    return data


def rename_according_to_time_and_date(data, confirmation):
    for dt_file_name, curr_file_names in data.items():
        counter = 0
        for curr_file_name in curr_file_names:
            counter += 1
            ext = os.path.splitext(curr_file_name)[1]
            if (len(curr_file_names) > 1):
                new_name = "%s-%d%s" % (dt_file_name, counter, ext)
            else:
                new_name = "%s%s" % (dt_file_name, ext)
            do_rename(curr_file_name, new_name, confirmation)


def main():
    confirmation, hour_offset = process_input_args(sys.argv[1:])
    data_source_func = partial(os.listdir, os.getcwd())
    data = get_file_rename_data(data_source_func, hour_offset)
    rename_according_to_time_and_date(data, confirmation)
    if not confirmation:
        print("\n\nrun with '-c' to really perform files renaming.\n")


if (__name__ == "__main__"):
    main()
