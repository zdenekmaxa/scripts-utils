#!/usr/bin/env python

"""
Script goes recursively through the directory tree starting from the current
directory and creates MD5_FILE text file containing md5 checksums of the
files present in a directory.

Author: Zdenek Maxa

"""


import os
import sys


MD5_FILE = "md5.log"



try:
    for root, dirs, files in os.walk(os.getcwd()):
        print("processing '%s' ..." % root)
        if MD5_FILE in files:
            print("file '%s' in '%s', removing it, generating a "
                  "new one ..." % (MD5_FILE, root))
            os.remove(os.path.join(root, MD5_FILE))
            files.remove(MD5_FILE)
        if len(files) > 0:
            print("changing directory to '%s', generating md5 ..." % root)
            curDir = os.getcwd()
            os.chdir(root)
            for f in files:
                os.system("md5sum \"%s\" >> md5.log" % f)
            print("changing directory to '%s'" % curDir)
            os.chdir(curDir)
        print("%s\n" % (78 * '-'))
except KeyboardInterrupt:
    print "ctrl-c caught, exit"
    sys.exit()
