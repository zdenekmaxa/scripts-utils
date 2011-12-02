#!/usr/bin/env python

# renames all files in the dictionary according to the creation
# date and time of the files
# example of destination name: p7261528.jpg  ->  2006-07-26-wed-14-32-44.jpg


import time
import sys
import os



def getNewFileName(oldFileName):
    """Creates the file name according to OS creation date and time."""

    days = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    newName = "%(year)d-%(month)d-%2(day)d-%(dow)s-%2(hour)d-%2(min)d-%2(sec)d"
    
    tNum = os.path.getmtime(oldFileName)
    t = time.localtime(tNum)
    hour = t[3] # could do hour correction here: t[3] +- 1

    name = "%d-%02d-%02d-%s-%02d-%02d-%02d" % (t[0], t[1], t[2], days[t[6]],
                                               hour, t[4], t[5])

    ext = oldFileName[-4:] # get file extension (including dot)
    result = "".join([name, ext.lower()])
    return result

# getNewFileName() ----------------------------------------------------------    


def createNewFileNames(srcList):
    """Creates an dictionary with key: new file name. If duplicates are
       detected (identical destination new file names, suffixes -xx are added
       to the file name). value: old file name as taken from srcList.
    """

    # dictionary to watch duplicates
    # key: new file name (as returned by getNewFileName()) - just based on
    # date and time ; value: counter of files with the same date and time,
    # counter will be added the final new name
    dupl = {}

    # result dictionary key: new file name ; value: old file name
    res = {}

    for old in srcList:
        new = getNewFileName(old)

        # check for duplicates
        if dupl.has_key(new):
            dupl[new] += 1 # increase counter
            print ("destination file name %s already exists, counter: %s" % 
                  (new, dupl[new]))
        else:
            dupl[new] = 1

        if res.has_key(new):
            # duplicate detected, will need to add suffix -01 (the first one)
            # this is to handle previous occurence in the res dictionary
            nameArray = new.split('.') # get file name and extension
            newName = "%s-01.%s" % (nameArray[0], nameArray[1])
            oldName = res.pop(new)
            res[newName] = oldName

        # store 'new' into result dictionary
        if dupl[new] > 1:
            nameArray = new.split('.') # get file name and extension
            newName = "%s-%02d.%s" % (nameArray[0], dupl[new],
                    nameArray[1])
            res[newName] = old
        else:
            res[new] = old

    return res

# createNewFileNames() ------------------------------------------------------    


def main():
    
    # if perform is set, will try to rename files, otherwise just print names
    perform = False 
    if len(sys.argv) > 1:
        if sys.argv[1] == "-c":
            perform = True
    
    # get list of files from the (source) current directory
    srcList = os.listdir(os.getcwd())

    # get dictionary key: new file name ; value: old file name (duplicates
    # handled)
    d = createNewFileNames(srcList)

    print "\n"
   
    keys = d.keys()
    keys.sort()
    for newName in keys:
        oldName = d[newName]
        
        newFinalName = newName
        if os.path.exists(newName):
            print ("%s exists in directory, names concatenated ... "
                   "(should not occur!)" % newName)
            newFinalName += oldName

        print "renaming %s -> %s" % (oldName, newFinalName)

        # factual rename
        try:
            if perform:
                os.rename(oldName, newFinalName)
        except IOError, ex:
            print "could not rename %s -> %s, reason: %s" % (oldName,
                    newFinalName, ex)

    if not perform:
         print "\n\nexecute with '-c' command option to rename files\n" 


# ---------------------------------------------------------------------------
if(__name__ == "__main__"):
    main()
# ---------------------------------------------------------------------------

