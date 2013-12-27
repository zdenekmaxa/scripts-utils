#!/usr/bin/env python

"""
Wrapper around GNU gpg program
Usage: run with --help

gpg <file.ext> -> encrypts file and creates file.ext.gpg
gpg <file.gpg> -> prompts for password and decrypts file

Automatic deletion of the original file is not implemented (yet).

More: --help

"""

import os
import sys
import subprocess
import tempfile


def printHelp():
    print  """
Simple wrapper around GNU gpg program to encrypt/decrypt files. Takes
exactly one argument on the command line - the file to encrypt / decrypt.

Decription is done if file has .gpg extension, encryption otherwise.
Entension .gpg is added automatically when encrypting a file.
"""


def encrypt(input):
    """
    Encryption adds automatiaclly .gpg extension to the input file.
    Does not remove the original file automatically.
    
    """
    # encrypt command
    ec = "/usr/bin/gpg -v --output %(output)s --encrypt " \
            "--recipient zdenekmaxa@yahoo.co.uk"
            # < %(input)s" - is provided otherwise

    output = "".join([input, ".gpg"])
    if os.path.exists(output):
        print "File '%s' exists, exit." % output
        sys.exit(1)

    c = ec % { "output" : output }
    print ("Running command: '%s' [input file '%s' provided] ... " % (c,
            input)),
    inputFile = open(input, "rb")

    try:
        subprocess.check_call(c.split(), stdin = inputFile, close_fds = False)
    except subprocess.CalledProcessError, ex:
        print "error was raised, see output ... ",
    
    print "finished."
    inputFile.close()
    print "\nDone\nDon't forget to remove the original file."


def decrypt(input):
    """
    Expects input being the file name in form 'filename.gpg'
    Output will be 'filename'
    Does not remove the original file automatically.
    
    """
    # decrypt command
    dc = "/usr/bin/gpg -v --output %(output)s --decrypt %(input)s"

    output = input[:-4] # without the .gpg extension
    if os.path.exists(output):
        print "File '%s' exists, exit." % output
        sys.exit(1)

    c = dc % { "output" : output, "input" : input }
    print "Running command: '%s' ... " % c,

    stdOut = tempfile.TemporaryFile("w+")
    try:
        subprocess.check_call(c.split(), stdout = stdOut, close_fds = False)
    except subprocess.CalledProcessError, ex:
        print "error was raised, see output ... ",
    
    print "finished."
    stdOut.seek(0)
    sys.stdout.write(stdOut.read())
    print "\nDone.\nDon't forget to remove the original file."


def main():
    inputFile = ""
    if len(sys.argv) > 1:
        if sys.argv[1] == "-h":
            printHelp()
            sys.exit(0)
        else:
            inputFile = sys.argv[1]
    else:
        print "%s wrapper around GNU gpg program, try -h" % sys.argv[0]
        sys.exit(0)

    try:
        open(inputFile, 'r')
    except IOError, ex:
        print "Can't open file %s, reason: %s" % (inputFile, ex)
        sys.exit(1)

    ext = inputFile[-4:] # get file extension (including dot)
    if ext == ".gpg":
        print "File has .gpg extension, thus going to decrypt it ..."
        decrypt(inputFile)
    else:
        print "File has not got .gpg extension, thus going to ecrypt it ..."
        encrypt(inputFile)


if __name__ == "__main__":
    main()

