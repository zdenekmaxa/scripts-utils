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
import pprint


def printer(stream_out, what):
    number = 0
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
            number = analyzer[a]

    return number


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

    total_ok, total_failed = 0, 0
    dirs_with_failures = []
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
        print("running command: '%s' ... " % command)
        proc = subprocess.Popen(
                command.split(),
                stdout=std_out_sub,
                stderr=std_err_sub,
                close_fds=False)
        ret_code = proc.wait()
        if ret_code:
            print("command return code was %s, see output ..." % ret_code)
            dirs_with_failures.append(path)
        print("command finished, results:")

        total_ok += printer(std_out_sub, "stdout")
        _ = printer(std_err_sub, "stderr")

        os.chdir(current_dir)
        print("\n\n\nchanged to the original working directory '%s'\n\n\n" %
                current_dir)

    print("TOTAL:")
    print("sum maching entries: %s" % total_ok)
    print("directories with failed sums / missing files: %s" % 
            pprint.pformat(dirs_with_failures))


if __name__ == "__main__":
    main()

