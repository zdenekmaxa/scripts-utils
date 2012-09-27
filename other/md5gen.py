#!/usr/bin/env python

"""
Script goes recursively through the directory tree starting from the current
directory and creates CHECKSUM_FILE text file containing md5 checksums of the
files present in a directory. The depth where the CHECKSUM_FILE files are
generated is configurable.
Should an older CHECKSUM_FILE be found, it's copied into 
CHECKSUM_FILE.DATETIME.

Author: Zdenek Maxa

"""


import os
import sys
from optparse import OptionParser, TitledHelpFormatter, OptionError
import subprocess
from tempfile import TemporaryFile
import time


# name of the output MD5 sums file (it's not configurable through CLI)
CHECKSUM_FILE = "md5.log"



def generate_checksums(directories, curr_dir):
    """
    Runs a find + checksum generating command in each directory in the
    input list. If CHECKSUM_FILE already exists, it's saved in to a backup
    file.

    """
    generated_files = []
    top_dir_cmd = ("find -maxdepth 1 -type f -exec md5sum {} \; > "
                   "/tmp/%s ; mv /tmp/%s ." % (CHECKSUM_FILE, CHECKSUM_FILE))
    other_cmd = ("find -type f -exec md5sum {} \; > "
                 "/tmp/%s ; mv /tmp/%s ." % (CHECKSUM_FILE, CHECKSUM_FILE))
    try:
        for dir_name in directories:
            if dir_name in [".", "./"]:
                command = top_dir_cmd
            else:
                command = other_cmd
            os.chdir(dir_name)
            print("Processing directory '%s' ..." % dir_name)
            if os.path.exists(CHECKSUM_FILE):
                os.rename(CHECKSUM_FILE, "%s-%s" % (CHECKSUM_FILE,
                                                    time.time()))
            print("\t'%s'" % command)
            os.system(command)
            check_file = os.path.join(curr_dir, dir_name, CHECKSUM_FILE)
            if os.path.getsize(check_file) == 0:
                print("File %s is empty, erasing." % check_file)
                os.remove(check_file)
            else:
                generated_files.append(check_file)
            os.chdir(curr_dir)
    except KeyboardInterrupt:
        print "ctrl-c caught, exit"
        sys.exit()
    return generated_files


def process_cli_args(args):
    usage = __doc__
    form = TitledHelpFormatter(width=78)
    parser = OptionParser(usage=usage, formatter=form,
            add_help_option=None)
    define_cli_options(parser)
    # opts - new processed options
    # args - remainder of the input array
    opts, args = parser.parse_args(args=args)
    if opts.max_depth < 1:
        print("--depth argument must be greater than 1")
        sys.exit(1)
    return opts


def define_cli_options(parser):
    help = "Display this help"
    parser.add_option("-h", "--help", help=help, action='help')
    help = "Directory depth to generate '%s' files at." % CHECKSUM_FILE
    parser.add_option("-d", "--depth", action="store", type="int",
            dest="max_depth", default=sys.maxint, help=help)


def get_directories(start_dir, find_command):
    """
    Runs a find command and returns a list of directories, checks
    output for sanity (whether it really is an existing directory).
    
    """
    def print_logs(stdout, stderr):
        stdout.seek(0) # move pointer back to beginning before read()
        stderr.seek(0)
        delim = 78 * '-'
        print("%s\nstdout:\n%s\n%s\nstderr:\n%s\n%s" % (delim, stdout.read(),
            delim, stderr.read(), delim))

    print("Running command '%s' ..." % find_command)
    stdout, stderr = TemporaryFile("w+"), TemporaryFile("w+")
    try:
        proc = subprocess.Popen(find_command.split(),
                stdout=stdout, stderr=stderr)
    except Exception as ex:
        print("Exception occured when executing the command, reason: %s" % ex)
        sys.exit(1)

    try:
        returncode = proc.wait()
    except Exception as ex:
        print("Exception occured (logs below), reason: %s" % ex)
        print_logs(stdout, stderr)
        sys.exit(1)
    
    if returncode == 0:
        print("Command finished.")
        stdout.seek(0) # move pointer back to beginning before read()
        # assuming each line of in the output is a returned directory name
        dirs = [d.strip().replace("./", "") for d in stdout.readlines() \
                    if os.path.exists(d.strip())]
        return dirs
    else:
        print("Command '%s' failed, return code: %s" % (find_command,
            returncode))
        print_logs(stdout, stderr)
        sys.exit(1)

    
def main():
    opts = process_cli_args(sys.argv)
    if opts.max_depth != sys.maxint:
        get_directories_cmd = "find -maxdepth %i -type d" % opts.max_depth
    else:
        get_directories_cmd = "find -type d"
    
    curr_dir = os.getcwd()
    print("Getting a list of dirs to operate in below %s ..." % curr_dir) 
    directories = get_directories(curr_dir, get_directories_cmd)
    generated_checksum_files = generate_checksums(directories, curr_dir)
    print("\n\nGenerated '%s' files (%s):" % (CHECKSUM_FILE, 
        len(generated_checksum_files)))
    for f in generated_checksum_files:
        print("\t%s" % f)


if __name__ == "__main__":
    main()
