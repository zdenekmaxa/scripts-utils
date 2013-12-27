#!/usr/bin/env python 

"""
Generates index.html file for picture web gallery.
To be run in a directory with pictures of the final size, thumbnails
are generated automatically using nconvert utility. Thus this script depends
on external nconvert utility.

Title of the page and background image should be edited by hand.

"""


import os
import popen2
import sys
import fnmatch
import traceback
import getopt



OUTPUT_FILE = "index.html"
DEBUG = True
TITLE = "x-max gallery"
WIDTH_THUMB = 190
HEIGHT_THUMB = 140
WIDTH_FULL = 1024
HEIGHT_FULL = 768
NUMBER_OF_COLUMNS = 3
TARGET_REFERENCE = "target=\"picture\""
PICTURES_SUBDIRECTORY = None


# getting more information from nconvert: -v (verbose)
CONVERSION_UTILITY = "/usr/local/bin/nconvert -ratio -resize %(width)s " \
        "%(height)s -out jpeg -o %(outputFile)s %(inputFile)s"




def resize(pics, width, height, command):
    """
    Resize pictures in pics (dictionary containing key - source file name
    and value - target file name) to width and heigth using command. If
    source and target file name are the same - erase the original file and
    store the new resized file under its name.
    
    """
    eraseOriginal = False

    for key in pics:
        source = key
        target = pics[key]
        if source == target:
            sourceNew = "".join(["original_to_erase-", source])
            print "rename: %s -> %s" % (source, sourceNew)
            os.rename(source, sourceNew)
            source = sourceNew
            eraseOriginal = True
        d = {"width" : width, "height" : height, "inputFile" : source,
             "outputFile" : target}
        cmd = command % d
        
        # too fast and subsequent erase makes the files unavailable
        # popen2.Popen3(cmd)
        # os.popen() waits for result
        print "resize command: %s" % cmd
        os.popen(cmd)
        if eraseOriginal:
            print "erase file: %s" % source
            os.remove(source)
        
        print "\n",


def createHTMLTable(pics, numberOfColumns, target = "", subdir = None):
    """
    createHTMLTable
    pics is a dictionary with files names. picture : picture-thumbnail
    
    """
    result = ""

    if subdir:
        subdir = "".join([subdir, '/'])
    else:
        subdir = ""

    template = ("\t<td><a href=\"%(subdir)s%(picture)s\" %(target)s>\n"
                "\t\t<font color=\"black\"><img border=\"2\" "
                "src=\"%(subdir)s%(thumbnail)s\">\n"
                "\t</a></td>\n")
             
    counter = 0
    keys = pics.keys()
    keys.sort()
    for key in keys:
        if counter == 0:
            result = "".join([result, "\t<tr>\n"])

        templateDir = { "subdir": subdir, "picture": key, "target": target,
                        "thumbnail": pics[key] }
        tmp = template % templateDir
        result = "".join([result, tmp])
        counter += 1
        if counter == int(numberOfColumns):
            counter = 0
            result = "".join([result, "\t</tr>\n"])

    # if counter is not true (first condition) it is 0, and </tr> has just
    # been put above, don't want to have it twice
    if counter and counter < numberOfColumns:
        result = "".join([result, "\t</tr>\n"])

    return result


def getListOfFiles(path = '.', fileMask = '*'):
    """Returns a list of files (not links or directories) in a specified
       directory 'path' and check every item whether it matches 'fileMask'.
       Non-recursive.
    """

    result = []
    everything = os.listdir(path)
    for i in everything:
        if os.path.isfile(i) and not os.path.islink(i) \
                and fnmatch.fnmatch(i, fileMask):
            result.append(i)

    return result


def getPageTemplate():

    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>%(title)s</title>

<style type="text/css">

body {
  font: 90%% 'Lucida Grande', Verdana, Geneva, Lucida, Arial, Helvetica, sans-serif;
  color: black;
  margin: 1em;
  padding: 1em;
}


h1 {
  text-decoration: none;
  color: black;
  background-color: transparent;
}


p {
  margin: 0.5em 0 1em 0;
  line-height: 1.5em;
}

h1, h2, h3, h4, h5, h6 {
  color: #003a6b;
  background-color: transparent;
  font: 100%% 'Lucida Grande', Verdana, Geneva, Lucida, Arial, Helvetica, sans-serif;
  margin: 0;
  padding-top: 0.5em;
}

h1 {
  font-size: 300%%;
  margin-bottom: 0.5em;
  color: black;
  border-bottom: 1px
}
h2 {
  font-size: 140%%;
  margin-bottom: 0.5em;
  border-bottom: 1px solid #aaa;
}
h3 {
  font-size: 130%%;
  margin-bottom: 0.5em;
}
h4 {
  font-size: 110%%;
  font-weight: bold;
}
h5 {
  font-size: 100%%;
  font-weight: bold;
}
h6 {
  font-size: 80%%;
  font-weight: bold;
}

</style>

</head>

<body background="background.jpg">

    <div>
        <h1>
            %(title)s
        </h1>
    </div>
    <!-- <img src="title.gif"> -->
    <p>
    <p>
    <p>
    <table width="80%%" cols="%(tableColumns)s" align="center">
    %(picTable)s
    </table>
    <p>
    <hr>
    <p>
</body>
</html> 
"""


def printUsage(name):
    global TARGET_REFERENCE

    print "Wrong parameters."
    print "\t -f\t specify file mask, otherwise is \"*\" (use quotation)"
    print "\t -r\t resize original files, otherwise create only thumbnails"
    print "\t -c\t number of columns in the html table (default is 3)"
    print ("\t -t\t do not add target refence %s to links "
          "(for framed-gallery page)" % TARGET_REFERENCE)
    print "\t -s\t pictures will be located in subdirectory"
    print "\nExamples:\n\t%s \"*.jpg\"\n\t%s \"*\" -r -s pics" % (name, name)


def getOptions(argv):
    global NUMBER_OF_COLUMNS, TARGET_REFERENCE, PICTURES_SUBDIRECTORY

    programName = os.path.split(argv[0])[1] # get program name
    mask = "*"
    resizeOriginal = False
    numberOfColumns = NUMBER_OF_COLUMNS
    target = TARGET_REFERENCE
    subdirectory = PICTURES_SUBDIRECTORY
    
    try:
        options, arguments = getopt.getopt(argv[1:], "hf:rc:ts:")
    except getopt.GetoptError:
        printUsage(programName)
        sys.exit(1)
    else:
        for opt, arg in options:
            if opt in ("-h", "--help"):
                printUsage(programName)
                sys.exit(0)
            elif opt in ("-f", "--files"):
                mask = arg
            elif opt in ("-r", "--resize"):
                resizeOriginal = True
            elif opt in ("-c", "--columns"):
                numberOfColumns = arg
            elif opt in ("-t", "--target"):
                target = ""
            elif opt in ("-s", "--subdirectory"):
                subdirectory = arg

    return (mask, resizeOriginal, numberOfColumns, target, subdirectory)


def main():
    global TITLE, WIDTH_THUMB, HEIGHT_THUMB, \
            WIDTH_FULL, HEIGHT_FULL, CONVERSION_UTILITY, DEBUG, OUTPUT_FILE

    # process command line options
    (mask, resizeOriginal, numberOfColumns, target, 
            subdirectory) = getOptions(sys.argv)

    # list of files (full path) from the current directory
    pics = getListOfFiles(path = os.curdir, fileMask = mask)

    # create temporary dictionary containing file names
    tmpPics = {}
    for p in pics:
        tmpPics[p] = p

    # resise to full size - if target name == source name -> delete original
    if resizeOriginal:
        try:
            resize(tmpPics, WIDTH_FULL, HEIGHT_FULL, CONVERSION_UTILITY)
        except Exception, why:
            print "Could not resize pictures to full size.\n%s" % why
            if DEBUG:
                trace = traceback.format_exception(*sys.exc_info())
                traceString = '\n '.join(trace)
                print "ERROR:\n%s\n" % traceString
            sys.exit(1)

    # create names of thumbnail files and store both into dictionary
    thumbPics = {}
    for p in pics:
        # file name without extension [:-4] + thumb + extension
        thumbPics[p] = "".join([p[:-4], "-thumb.jpg"])

    # create thumbnails - resize and keep original files
    try:
        resize(thumbPics, WIDTH_THUMB, HEIGHT_THUMB, CONVERSION_UTILITY)
    except Exception, why:
        print "Could not resize pictures to thumbnail size.\n%s" % why
        if DEBUG:
            trace = traceback.format_exception(*sys.exc_info())
            traceString = '\n '.join(trace)
            print "ERROR:\n%s\n" % traceString
        sys.exit(1)
   
    # create HTML table
    tableBody = createHTMLTable(thumbPics, numberOfColumns, target,
                                subdirectory)

    # interpolate with template
    result = getPageTemplate() % {"title" : TITLE, "title" : TITLE,
            "tableColumns": NUMBER_OF_COLUMNS, "picTable" : tableBody }

    # print on the standard output
    print "result page written into %s file" % OUTPUT_FILE
    f = open(OUTPUT_FILE, 'w')
    f.write(result)
    f.close()


if __name__== "__main__":
        main()

