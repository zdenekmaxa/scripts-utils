#!/usr/bin/env python

"""
System backup script (driven by XML configuration file).
Usage: run with --help

TODO:
    (o) testing via py.test
    (o) list of particularly specified files (notes, etc) to be copied in
        to an extra directory (will need to create corresponding XML
        section)? 
    (o) tar command to output "progress" (like ascii progress bar)?
    (o) multithreaded / multiprocess running tar, gzip, gzip test
        commands to be packed into a single Command instance (rather
        than each of these being a single Command instance) and these
        new instances could then potencially be processed in parallel
        by the Executor class
    (o) to change the rights ... ?
            chgrp xmax backupdir ; chmod o-w,o-r,o-x,g+w backupdir
    (o) implement loggger differently, just log, does it have to be
        method attribute?
    (o) revise flow and error states, do not always terminate, just log
        and warn loudly and examine (best in a py.test unittest) the most
        common error state: failed verify command

Author: Zdenek Maxa

"""


import sys
import os
import datetime
import logging
import getopt
import time
import subprocess
import tempfile
import shutil
# specific imports
try:
    from pyxmaxlibs import helpers
    from pyxmaxlibs.logger import Logger
    import lxml.objectify
except ImportError, ex:
    print "Cannot import necessary Python modules, reason: %s" % ex
    sys.exit(1)


class Executor(object):

    def __init__(self, dstDir, logger):
        self.dstDir = dstDir
        self.logger = logger

    def _storeStdOutput(self, command, toStore):
        """
        Store stdouput for a command, now held in data into file
        command.getStdOutLogFile()
        toStore is a tempfile and should be open.
        
        """
        logFile = command.getStdOutLogFile()
        self.logger.debug("Storing command stdout into file '%s'" % logFile)
        logPrefix = command.getLogPrefix()
        try:
            f = open(logFile, 'a')  # append from all commands
            f.write(logPrefix)
            toStore.flush()
            f.write(toStore.read())
            f.flush()
            f.close()
        except OSError, ex:
            m = ("Error while storing stdoutput into file '%s', "
                 "reason: %s" % (logFile, ex))
            raise Exception(m)
    
    def execute(self, commands):
        strComm = "\t".join(["'%s'\n" % c.getCommand() for c in commands])
        self.logger.info("%s command(s) to be executed:\n\t%s" %
                         (len(commands), strComm))

        for c in commands:
            comm = c.getCommand()
            # create tmp files for stdOut, stdErr of the process
            stdOut = tempfile.TemporaryFile("w+") # read / write
            stdErr = tempfile.TemporaryFile("w+")
            try:
                self.logger.debug("Changing current directory to '%s'" %
                                  c.getChangeToDir())
                os.chdir(c.getChangeToDir())
                self.logger.info("Executing command:\n\t'%s' ..." % comm)
                
                # p = subprocess.Popen() will not wait, would then use
                # retCode = p.wait() - here consider multithreading
                
                # check_call() waits for the call, if returncode is non
                # zero, CalledProcessError is raised
                # subprocess.Popen() requires arguments in a sequence, if run
                # with shell=True argument then could take the whole string
                p = subprocess.check_call(comm.split(),
                                          stdout=stdOut,
                                          stderr=stdErr,
                                          close_fds=False)
                self.logger.info("Command finished, no error raised.")

                # store stdOut, stdErr
                # move pointer back to beggining before read()
                stdOut.seek(0) 
                stdErr.seek(0)
                stdOutMsg = ""
                if c.getStdOutLogFile():
                    # stdoutput file is set for a command, store output there
                    self._storeStdOutput(c, stdOut)
                    stdOutMsg = ("stdout: saved in a separate file '%s'" %
                                 c.getStdOutLogFile())
                else:
                    stdOutMsg = "\nstdout:\n%s" % stdOut.read()

                self.logger.debug("%s\nstderr:\n%s" %
                                  (stdOutMsg, stdErr.read()))

            except subprocess.CalledProcessError, ex:
                stdOut.seek(0)
                stdErr.seek(0)
                self.logger.debug("\nstdout:\n%s\n\nstderr:\n%s" %
                                  (stdOut.read(), stdErr.read()))
                m = ("'%s' failed, return code: %s, reason: %s" %
                     (comm, ex.returncode, ex))
                self.logger.error(m)
                # just log, do not terminate the whole process
                #raise Exception(m)


class XMLInputProcessor(object):
    """
    Converts XML input configuration file into list of commands,
    i.e. list of Command class.

    """

    def __init__(self, fileName, destDir, logger):
        self.logger = logger
        # XML config file to parse
        self.fileName = fileName
        # destination directory
        self.destDirFullPath = destDir
    
    def getCommands(self, changeTo, dest, dir):
        """
        According to input arguments creates a list of Commands
        (class Command) for each predefined command (actions field).
        dir is dictionary representing <dir> XML element
        keys: archiveName - name of the archive
              srcDir - source directory for the archive
              actions - comma separated list of predefined commands
              exclude - comma separated list of directories to exclude
                        (argument to --exclude tar option).
        actions.split(',')[0] - is expected to be tar command
                          [1] - gzip (create archive) command (optional)
                          [2] - gzip (test archive) command (optional)

        """
        commands = None
        srcDir = dir.get("srcDir", None)
        archiveName = dir.get("archiveName", None)
        actions = dir.get("actions", None)
        exclude = dir.get("exclude", None)

        if not srcDir and not actions:
            return commands
        
        # continue
        commands = [] # list of commands - result

        if not archiveName:
            archiveName = srcDir
        
        tarArchiveFullPath = os.path.join(self.destDirFullPath, dest,
                                         "".join([archiveName, ".tar"]))

        ac = actions.split(',') # predefined comma separated commands
        if len(ac) >= 1:
            # only tar command in the action attribute ...
            c = Command(changeTo)
            if exclude:
                e = exclude.split(',')
                ex = "".join(["--exclude %s " % i.strip() for i in e])
            else:
                ex = ""
            d = {"archive": tarArchiveFullPath,
                 "dir": srcDir,
                 "exclude": ex}
            command = ac[0].strip() % d
            c.setCommand(command)
            c.setStdOutLogFile(os.path.join(self.destDirFullPath,
                               "archive-filelist.log"))
            c.setLogPrefix("".join(["\n", 78 * '=', "\n", command,
                           "\n", 78 * '=', "\n"]))
            commands.append(c)
        if len(ac) == 3:
            # gzip command 
            c = Command(changeTo)
            d = {"archive": tarArchiveFullPath}
            c.setCommand(ac[1].strip() % d)
            commands.append(c)
            
            # gzip integrity test command
            c = Command(changeTo)
            d = {"zipArchive": "".join([tarArchiveFullPath, ".gz"])}
            c.setCommand(ac[2].strip() % d)
            commands.append(c)

        return commands

    def process(self):
        """
        Process XML configuration input and return corresponding
        backup commands for execution.

        """
        r = [] # result - list of commands
        self.logger.info("Parsing '%s' file." % self.fileName)
        feed = lxml.objectify.parse(self.fileName)
        root = feed.getroot()
        commonsList = root.getchildren()
        self.logger.debug("%d 'commonDirs' sections found." %
                          len(commonsList))

        for common in commonsList: # iterate over <commonDirs>
            dest = common.get("destination", None)
            changeTo = common.get("changeTo", None)
            # test for None necessary
            if dest and changeTo:
                #print "   ", changeTo, "  ", dest
                self.logger.debug("%d 'dirs' sections found." %
                                  common.countchildren())
                for dir in common.getchildren(): # iterate over <dir>
                    currCommands = self.getCommands(changeTo, dest, dir)
                    if currCommands:
                        r.extend(currCommands) # will keep order
                    (name, actions, exclude) = (None, None, None)

                # if the destination directory does not exist, create it
                destCheck = os.path.join(self.destDirFullPath, dest)
                if not os.path.exists(destCheck):
                    self.logger.info("Creating directory '%s'" % destCheck)
                    os.mkdir(destCheck)
            (dest, changeTo) = (None, None)
        
        return r


class Command(object):

    def __init__(self, changeToDir):
        # directory into which to change before execution
        self.changeToDir = changeToDir
        # the command itself
        self.command = None
        # file name to put stdoutput of successful running
        self.stdOutLogFile = None
        # stdOutLogFile is open for appending, this is prefix of
        # consecutive additions
        self.logPrefix = ""

    def setCommand(self, command):
        self.command = command

    def setStdOutLogFile(self, stdOutLogFile):
        self.stdOutLogFile = stdOutLogFile

    def setLogPrefix(self, logPrefix):
        self.logPrefix = logPrefix
    
    def getChangeToDir(self):
        return self.changeToDir

    def getCommand(self):
        return self.command
    
    def getStdOutLogFile(self):
        return self.stdOutLogFile

    def getLogPrefix(self):
        return self.logPrefix


class Backupper(object):
    """
    Main class. Its components - Logger, Executor, etc.
    
    """

    def __init__(self, xmlConfigFile, destDir):
        # destination directory for backup
        self.dstDir = destDir
        # XML configuration of the backup process
        self.xmlConfig = xmlConfigFile
        # name of the file to store logging into
        self.logFileName = "backup.log"
        self.finalArchivesMask = "*.tar*"
        self.md5checksumFileName = "md5checksum.log"
        # start time of the process to measure total time
        self.startTime = datetime.datetime.now()
        
        # init logger
        logFile = os.path.join(self.dstDir, self.logFileName)
        # tell logging which logger to instantiate
        logging.setLoggerClass(Logger)
        self.logger = Logger(log_file=logFile, level=logging.DEBUG)

        # init commands executor
        self.executor = Executor(self.dstDir, self.logger)

        self.logger.info("Start time: %sh %sm %ss" % (self.startTime.hour,
            self.startTime.minute, self.startTime.second))

    def generateMD5Sums(self):
        """
        Generate md5sums of archives - using finalArchivesMask From input
        file name takes only file name and last directory (practical to
        have only the last directory compoment in the log file - for later
        checking - traversing directories and executing md5sum file.

        """
        # returns full paths of files
        files = helpers.get_files(path=self.dstDir,
                                  file_mask=self.finalArchivesMask,
                                  recursive=True)
        for f in files:
            # get last two components of path, e.g. 'system/etc.tar.gz'
            # remove dstDir from the file's full path
            relatName = f.replace(self.dstDir, "")
            if relatName[0] == os.path.sep:
                relatName = relatName[1:] # remove leading / if there is
            c = Command(self.dstDir) # this is working dir for the command
            c.setCommand("md5sum %s" % relatName)
            c.setStdOutLogFile(os.path.join(self.dstDir,
                                            self.md5checksumFileName))
            self.executor.execute([c])

    def copyFiles(self):
        """
        Copies this scripts itself and all found XML configuration
        files into the destination backup directory.

        """
        # current dir hasn't been changed yet, sys.argv[0] holds
        # correct path (this method should have been call right at start)
        self.logger.info("Copy this script '%s' to '%s'" %
                         (sys.argv[0], self.dstDir))
        # last access time and last modif time are copied as well (cp -p)
        shutil.copy2(sys.argv[0], self.dstDir)
        # get list of XML config files
        xmlPath = os.path.dirname(os.path.abspath(self.xmlConfig))
        
        xmlConfigFiles = helpers.get_files(path=xmlPath, file_mask="*.xml")

        for xmlFile in xmlConfigFiles:
            self.logger.info("Copy file '%s' to '%s'" %
                             (xmlFile, self.dstDir))
            shutil.copy2(xmlFile, self.dstDir)

    def backup(self):
        """
        main backup method.
        exception checking is better here in top level caller.
        on this level is better to break up particular call rather than
        accumulate them together.

        """
        # copy files (script, XML config files)
        try:
            self.copyFiles()
        except Exception, ex:
            self.logger.error("Copy failed, reason: %s" % ex)
            self.finish(retCode=1)

        # parse / process XML input and generate backup commands
        try:
            xmlProc = XMLInputProcessor(self.xmlConfig,
                                        self.dstDir,
                                        self.logger)
            commands = xmlProc.process()
        except Exception, ex:
            m = "Error while processing input file, reason: %s" % ex
            self.logger.fatal(m)
            self.finish(retCode=1)

        # execute backup commands - commands list run as externally
        try:
            self.executor.execute(commands)
        except Exception, ex:
            self.logger.fatal("Executing commands failed, reason: %s" % ex)
            self.finish(retCode=1)

        # MD5 checksums generation
        try:
            self.generateMD5Sums()
        except Exception, ex:
            self.logger.fatal("Error generating md5sums, reason: %s" % ex)
            self.finish(retCode=1)

        # dpkg Debian packages listings
        try:
            c = Command(self.dstDir) # set working directory, here unimportant
            c.setCommand("dpkg --get-selections")
            c.setStdOutLogFile(os.path.join(self.dstDir,
                                            "dpkg--get-selections.log"))
            self.executor.execute([c])
            # set working directory, here unimportant
            c = Command(self.dstDir) 
            c.setCommand("dpkg -l")
            c.setStdOutLogFile(os.path.join(self.dstDir, "dpkg-l.log"))
            self.executor.execute([c])
        except Exception, ex:
            self.logger.fatal("Error while running dpkg, reason: %s" % ex)
            self.finish(retCode=1)

    def finish(self, retCode=0):
        endTime = datetime.datetime.now()
        self.logger.info("Finish time: %sh %sm %ss" %
                         (endTime.hour, endTime.minute, endTime.second))
        duration = (endTime - self.startTime).seconds / 60 # duration in min
        self.logger.info("Backup lasted: %s minutes" % duration)

        del self.executor
        
        self.logger.close()
        del self.logger
        logging.shutdown()

        sys.exit(retCode)


def printUsage():
    print """
backupper.py

Backup utility. Creates a backup (tar archive, zip compression, consistency
checks, md5sums) of the directories as specified in the XML configuration
file. Destination directory and configuration file are mandatory arguments:

    -c, --config <XML configuration file>
    -d, --directory <destination directory to store archives into>
"""


def getOptions(inputArgs):
    """
    Process command line options and get destination directory and XML
    configuration file. Check validity of the arguments.

    """
    config = ""
    dstDir = ""

    try:
        options, args = getopt.getopt(inputArgs, "hc:d:",
                                      ["help", "config=", "directory="])
    except getopt.GetoptError:
        print "Incorrect command line options, try --help"
        sys.exit(1)
    else:
        for o, a in options: # a is argument
            if o in ("-h", "--help"):
                printUsage()
                sys.exit(0)
            elif o in ("-c", "--config"):
                config = a
                try:
                    f = open(config, 'r')
                    f.close()
                except IOError, ex:
                    print "Can't open file '%s', reason: %s" % (a, ex)
                    sys.exit(1)
            elif o in ("-d", "--directory"):
                dstDir = a
                if not (os.path.exists(dstDir) and os.path.isdir(dstDir)):
                    print ("'%s' is neither a directory or does not "
                           "exist, exit." % dstDir)
                    sys.exit(1)

    if not config or not dstDir:
        print "Mandatory arguments not provided, try --help"
        sys.exit(0)

    return (config, dstDir)


def main():
    print "%s backup script, raw arguments: %s" % (sys.argv[0], sys.argv[1:])

    # get XML configuration file and destination directory for the backup
    (config, dstDir) = getOptions(sys.argv[1:])
    print("Using XML configuration file: '%s', destination "
          "directory: '%s'" % (config, dstDir))

    # get date and time and create final destination directory
    dtFormat = "%Y-%m-%d-%Hh-%Mm-%Ss"
    dt = time.strftime(dtFormat, time.localtime()) # now
    dstDir = os.path.join(os.path.abspath(dstDir), "".join(["BACKUP-", dt]))
    print "Final destination directory: '%s'" % dstDir
    try:
        os.mkdir(dstDir)
    except OSError, ex:
        print "Could not create directory '%s', reason: %s" % (dstDir, ex)
        sys.exit(1)

    try:
        backupper = Backupper(config, dstDir)
    except Exception, ex:
        print ex
        sys.exit(1)

    # all exceptions are handled by the Backupper class itself
    backupper.backup()
    backupper.finish()

    
if __name__ == "__main__":
    main()

