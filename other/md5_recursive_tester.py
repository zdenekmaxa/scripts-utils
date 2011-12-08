#!/usr/bin/env python

"""
Script goes through the directory tree recursively and looks for files
that conform *md5* mask (in details: find ./ -iregex '.*md5.*' -print).
Then it runs md5sum -c <file> upon these files which are considered to
be output of previously run md5sum in the corresponding directory.

Author: Zdenek Maxa

"""


import os
import sys
import subprocess
import tempfile



def printer(outputStream, what):
    outputStream.seek(0)
    print("result (%s):" % what)
    analyzer = {"OK": 0,
                "FAILED open or read": 0,
                "No such file or directory": 0} 
    for line in outputStream.readlines():
        l = line.strip()
        toPrint = True
        for a in analyzer:
            if l.endswith(a):
                analyzer[a] = analyzer[a] + 1
                toPrint = False
        if toPrint:
            print l

    for a in analyzer:
        if analyzer[a]:
            print("'%s'-ending entries: %s" % (a, analyzer[a]))



def main():
    print("current directory: '%s'" % os.curdir)
    
    command = "find -iregex .*md5.* -print"
    stdOut = tempfile.TemporaryFile("w+")
    try:
        print("running command: '%s' ... " % command)
        subprocess.check_call(command.split(), stdout = stdOut,
                              close_fds = False)
    except subprocess.CalledProcessError as ex:
        print("error was raised, see output ... ")
    print("finished.\n")

    stdOut.seek(0)

    # store original working directory
    currDir = os.getcwd() 

    for line in stdOut.readlines():
        print(78 * '-')
        entry = line.strip()
        print("found entry: '%s'" % entry)
        path = os.path.dirname(entry)
        print("changing directory to '%s'" % path)
        os.chdir(path)

        fileName = os.path.basename(entry)
        command = "md5sum -c %s" % fileName
        
        stdOutSub = tempfile.TemporaryFile("w+")
        stdErrSub = tempfile.TemporaryFile("w+")
        try:
            print("running command: '%s' ... " % command)
            subprocess.check_call(command.split(), stdout = stdOutSub,
                    stderr = stdErrSub, close_fds = False)
        except subprocess.CalledProcessError as ex:
            print("error was raised, see output ... ")
        print("finished, printing results ...")

        printer(stdOutSub, "stdout")
        printer(stdErrSub, "stderr")

        os.chdir(currDir)
        print("\n\n\nchanged to the original working directory '%s'\n\n\n" %
                currDir)


if __name__ == "__main__":
    main()
