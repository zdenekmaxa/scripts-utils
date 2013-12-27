#!/usr/bin/env python
# (C) 2003 by Zdenek Maxa, <zdenek.maxa@email.cz>

"""
Erase or replace pattern in the names of files.

Usage ep.py --help

"""

import string, os, sys, getopt


debug = True


def printUsage():
    print """
ep - erase / replace patterns in the file names / directory names
options:
     o none        : by default it replaces all spaces by '_' character
     o -s <src>    : source subsring (replace mode: src_string -> dst_string)
     o -d <dst>    : dest. substring (replace mode: src_string -> dst_string)
     o -t          : (for tracklists) replaces first blank by '-' and all
                     the following spaces by '_' It's exclusive option
     o -r          : recursive in the directory subtree
     o -h --help   : this help info
"""


def getOptions():
    """returns command line options:
       default, tracklist, srcString, destString, recursive
    """

    # set default values of options
    tracklist = False
    recursive = False
    srcString = None
    dstString = None

    if len(sys.argv) > 0:
        try:
            options, arguments = getopt.getopt(sys.argv[1:], "htrs:d:")
        except getopt.GetoptError:
            print "Incorrectly specified command line options, try -h"
            sys.exit(1)
        else:
            for opt, arg in options:
                if opt in ("-h", "--help"):
                    printUsage()
                    sys.exit(0)
                elif opt in ("-t"):
                    tracklist = True
                elif opt in ("-r"):
                    recursive = True
                elif opt in ("-s"):
                    srcString = arg
                elif opt in ("-d"):
                    dstString = arg

    # -t is exclusive (doesn't work the others)
    if tracklist and (srcString or dstString):
        print "Incorrectly specified command line options, try -h"
        sys.exit(1)

    # return the values according to command line options
    return (tracklist, recursive, srcString, dstString)


def getFilesAndDirectoriesListRecursively(dir):

    listFilesDirs = []  # final list (contains all files and directories)

    for root, dirs, files in os.walk(dir):
        # don't do any check - put all files, dirs and links into the list
        l = [os.path.join(root, item) for item in dirs]  # full-path dirs
        listFilesDirs.extend(l)
        l = [os.path.join(root, item) for item in files] # full-path files
        listFilesDirs.extend(l)
    return listFilesDirs


def renameEntries(entriesList):
    for (src, dest) in entriesList:
        if src == dest:
            continue
        srcForPrint = "".join([src, "   "]).ljust(50, '-')
        print "mv:  %s-->   %s" % (srcForPrint, dest)
        try:
            os.rename(src, dest)
        except:
            print "Could not rename '%s' -> '%s', exit." % (src, dest)
            sys.exit(1)


def replacePatterns(srcList, old=' ', new='_', tracks=None):
    """
    argument tracks - distinguish whether operating upon tracklist or not
    
    """
    entriesList = []
    for src in srcList:
        # two items in the tuple added into list of entries
        if tracks == None:
            dest = src.replace(old, new)
        else:
            # if tracks is set, replace the first space occurance by '-'
            tmpString = src.replace(' ', '-', 1)
            dest = tmpString.replace(old, new)
        pair = (src, dest)
        entriesList.append(pair)
    return entriesList

    
def main():
    global debug

    (tracklist, recursive, srcString, dstString) = getOptions()
    if debug:
        print "\ncommand line options:\n", (tracklist, recursive, srcString,
                dstString)
        
    currDir = os.getcwd()
    if recursive:
        srcList = getFilesAndDirectoriesListRecursively(currDir)
    else:
        srcList = os.listdir(currDir)
    if debug:
        print "\n list to process:\n", srcList

    srcList.sort()

    if srcString == None and dstString == None:
        srcString = ' '
        dstString = '_'
    if tracklist:
        entriesList =  replacePatterns(srcList, srcString, dstString, 1)
    else:
        entriesList =  replacePatterns(srcList, srcString, dstString)
    if debug:
        print "\n tuple with patterns replaced:\n", entriesList
    
    renameEntries(entriesList)


if __name__ == "__main__":
    main()
