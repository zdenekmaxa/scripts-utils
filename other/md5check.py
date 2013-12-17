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



def printer(stream_out, what):
    stream_out.seek(0)
    print("result (%s):" % what)
    analyzer = {"OK": 0,
                "FAILED open or read": 0,
                "No such file or directory": 0} 
    for line in stream_out.readlines():
        l = line.strip()
        to_print = True
        for a in analyzer:
            if l.endswith(a):
                analyzer[a] = analyzer[a] + 1
                to_print = False
        if to_print:
            print l

    for a in analyzer:
        if analyzer[a]:
            print("'%s'-ending entries: %s" % (a, analyzer[a]))



def main():
    print("current directory: '%s'" % os.curdir)
    
    command = "find -iregex .*md5.* -print"
    std_out = tempfile.TemporaryFile("w+")
    try:
        print("running command: '%s' ... " % command)
        subprocess.check_call(command.split(), stdout = std_out,
                              close_fds = False)
    except subprocess.CalledProcessError as ex:
        print("error was raised, see output ... ")
    print("finished.\n")

    std_out.seek(0)

    # store original working directory
    current_dir = os.getcwd() 

    for line in std_out.readlines():
        print(78 * '-')
        entry = line.strip()
        print("found entry: '%s'" % entry)
        path = os.path.dirname(entry)
        print("changing directory to '%s'" % path)
        os.chdir(path)

        fileName = os.path.basename(entry)
        command = "md5sum -c %s" % fileName
        
        std_out_sub = tempfile.TemporaryFile("w+")
        std_err_sub = tempfile.TemporaryFile("w+")
        try:
            print("running command: '%s' ... " % command)
            subprocess.check_call(command.split(), stdout = std_out_sub,
                    stderr = std_err_sub, close_fds = False)
        except subprocess.CalledProcessError as ex:
            print("error was raised, see output ... ")
        print("finished, printing results ...")

        printer(std_out_sub, "stdout")
        printer(std_err_sub, "stderr")

        os.chdir(current_dir)
        print("\n\n\nchanged to the original working directory '%s'\n\n\n" %
                current_dir)


if __name__ == "__main__":
    main()
