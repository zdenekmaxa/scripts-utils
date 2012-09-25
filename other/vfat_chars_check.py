#!/usr/bin/env python

"""
vfat_chars_check

Walks through the directory tree starting from the current directory and
checks every found directory and file name if it conforms with the VFAT
filesystem allowed characters. Directory or files names which do not
conform (their file names contain characters other than those listed in
the help message) are printed.

Author: Zdenek Maxa

"""

import os, sys, string


# allowed vfat file names characters, inclusive lists, ascii ord values
ALLOWED_ORD_VALS = []
for sub_list in ((32, 35), (38, 41), (43, 46), (48, 57), (61, 61),
                 (65, 91), (93, 95), (97, 126)):
    # +1 include top
    ALLOWED_ORD_VALS.extend(range(sub_list[0], sub_list[1] + 1))


def print_help():
    print(__doc__)
    print("VFAT allowed characters:")
    s = ""
    c = 0
    for i in ALLOWED_ORD_VALS:
        s += "%03i %s   " % (i, chr(i))
        c += 1
        if c % 10 == 0:
            print(s)
            s, c = "", 0
    else:
        print(s)


def check_names(root, names):
    """
    Check input names if it conforms with VFAT allowed name characters.
    If it doesn't, the name is added into output list.

    """
    result = []
    for name in names:
        doesnt_conform = False
        for char in name:
            if ord(char) not in ALLOWED_ORD_VALS:
                doesnt_conform = True
        if doesnt_conform:
            result.append(os.path.join(root, name))
    return result 


def check_vfat_chars_in_filenames(start_directory):
    """
    Walk over all files in the specified directory start_directory.
    Return list of files and directories which do not conform with VFAT
    filesystem characters restrictions.

    """
    not_conforming_list = []
    try:
        for root, directories, files in os.walk(start_directory):
            print("Processing '%s' ..." % root)
            if len(files) > 0:
                print("Changing directory to '%s', ..." % root)
                curr_dir = os.getcwd()
                os.chdir(root)
                not_conforming_list.extend(check_names(root, files))
                not_conforming_list.extend(check_names(root, directories))
                print("Changing directory to '%s'" % curr_dir)
                os.chdir(curr_dir)
    except KeyboardInterrupt:
        print "Ctrl-c caught, exit"
    return not_conforming_list


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    curr_dir = os.getcwd()
    print("Checking VFAT conforming filenames in '%s' ...\n" % curr_dir)
    not_conforming_list = check_vfat_chars_in_filenames(curr_dir)
    print("\nResults (%s files/dirs containing VFAT forbidden chars):" %
            len(not_conforming_list))
    for item in not_conforming_list:
        print("\t%s" % item)

if __name__ == "__main__":
    main()
