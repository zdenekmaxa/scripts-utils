#!/usr/bin/env python

"""
f - wrapper around unix find utility
 
f "substring" [-d <where>]    searches for directories / files names 
                              containing substring in the directory where,
                              by default in the current directory
"""

# 2009-10-23 removed feature of reading patterns from a file
# 2009-10-23 white spaces handling inside regular expression search pattern

# TODO:
# don't list all files as separate entries if the sought pattern is found
# in the middle of the full path in a directory name (i.e. don't list all
# files below a directory in whose name the pattern was found) [this
# requirement involves python postprocessing of the results returned by find,
# otherwise merely calling findCommand would be sufficient]

# using find (see command in the performSearch() function):

# won't find pattern in a file which is hidden (starting with .)
# find $SEARCHPATH/ -iname "*$1*" -print

# finds both in a normal file name as well as in a file which is
# hidden ; unlike -regex is case insensitive
# find $SEARCHPATH/ -iregex ".*$1.*" -print


import os
import sys
import time
import getopt
import subprocess
import tempfile


def printUsage():

    print """
f - wrapper utility around find, by default searches current directory
    if filelist is specified, it takes a list of substrings to search from
    there

usage:
f "substring"  [-d, --directory directory_to_search_in]
"""


def getOptions(opt):
    whatToSearch = "" # substring to search
    whereToSearch = os.getcwd()  # get current working directory

    if(len(opt) < 1):
        print "No arguments provided, try --help"
        sys.exit(0)

    # is the first argument substring to be searched?
    if opt[0] not in ("-d", "--directory", "-h", "--help"):
        whatToSearch = opt[0]
        opt = opt[1:]
    # consider also situation f -d /mnt/data/ substring
    elif opt[0] in ("-d", "--directory"):
        try:
            whereToSearch = opt[1] 
            whatToSearch = opt[2]
        except IndexError:
            printUsage()
            print "Incorrect command line options"
            sys.exit(1)

    # standard scenario, command called: f substring [-d wheredirectory]
    try:
        options, args = getopt.getopt(opt, "hd:", ["help", "directory="])
    except getopt.GetoptError:
        print "Incorrect command line options, try --help"
        sys.exit(1)
    else:
        for o, a in options:
            if o in ("-h", "--help"):
                printUsage()
                sys.exit(0)
            elif o in ("-d", "--directory"):
                whereToSearch = a

    return (whatToSearch, whereToSearch)


def performSearch(what, where):
    """
    what - pattern which is sought
    where - searching path where
    execute external command findCommand for each item in what
    and catch output - list of entries for each pattern, result is list
    
    """
    # this command gets split later by white spaces, if search pattern
    # contains space, it will have problems
    command = "find %(where)s -iregex .*%(what)s.* -print"

    r = []

    # create tmp files for stdOut, stdErr of the process for read/write
    stdOut = tempfile.TemporaryFile("w+")
    stdErr = tempfile.TemporaryFile("w+")

    stdOut.truncate(0), stdErr.truncate(0)

    # move pointer to the beginning
    stdOut.seek(0), stdErr.seek(0)

    c = command % { "where" : where, "what" : what }
    print "executing command: \"%s\" ... " % c,
    
    try:
        subprocess.check_call(c.split(), stdout = stdOut, stderr = stdErr,
                close_fds = False)
    except subprocess.CalledProcessError, ex:
        print "error was raised, see output ... ",
    
    print "finished."

    # move pointer to the beginning
    stdOut.seek(0), stdErr.seek(0)
    r.extend(stdOut.readlines()), r.extend(stdErr.readlines())
    stdOut.close(), stdErr.close()

    return r


def main():
    (whatToSearch, whereToSearch) = getOptions(sys.argv[1:])

    # observed that path not ending with '/' was not successfullly
    # sought (find command nuance?)
    if not whereToSearch.endswith(os.sep):
        whereToSearch = whereToSearch + os.sep
    
    results = performSearch(whatToSearch, whereToSearch)

    print "searching directory: \"%s\"" % whereToSearch
    print "searching for pattern: \"%s\"" % whatToSearch
    print "results: %s" % len(results)
    print 78 * '-'

    results.sort()
    for i in range(len(results)):
        r = results[i].strip()

        # TODO: (2009-03-16) don't print r item if the
        # sought pattern was already present in previous (so it has
        # already been printed) - print just once trying via previous
        # variable. Nothing worked perfectly - the result output was
        # still either too redundant or eliminating entries it should
        # not have, so would be more damaging than helpful, thus
        # removing completely for now
        
        print "%s" % r


if __name__ == "__main__":
    main()
