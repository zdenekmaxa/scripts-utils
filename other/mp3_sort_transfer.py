"""
MP3 disk sort script.
Copies album folders from two source locations to a third, sorted one,
    into alphabetical subdirectories.
Run from the MP3 disk root.

"""


import os
import sys
import shutil


def process_dir(base_dir, dir_name, target_dir):
    """
    Process 1 album directory.
    Sort according it's initial letter and copy everything.

    """
    first_letter = dir_name[0].upper()
    # in case the first letter is not alphabetical, sort under letter A
    if ord(first_letter) not in range(ord("A"), ord("Z") + 1):
        first_letter = "A"
    target = os.path.join(target_dir, first_letter)
    if not os.path.exists(target):
        os.mkdir(target)
    src = os.path.join(base_dir, dir_name)
    dst = os.path.join(target, dir_name)
    print "%s -> %s" % (src, dst)
    if os.path.exists(dst):
        print "WARNING: %s exists already, skipping." % dst
    else:
        shutil.copytree(src, dst)


def process_base_dir_1(dir_to_process, target_dir):
    base_dir_name = os.path.join(os.getcwd(), dir_to_process)
    os.chdir(base_dir_name)
    for name in sorted(os.listdir(os.getcwd())):
        if os.path.isdir(name):
            #print name
            process_dir(base_dir_name, name, target_dir)
    os.chdir("..")


def process_base_dir_2(dir_to_process, target_dir):
    base_dir_name = os.path.join(os.getcwd(), dir_to_process)
    os.chdir(base_dir_name)
    for disk_dir in sorted(os.listdir(os.getcwd())):
        os.chdir(disk_dir)
        for name in sorted(os.listdir(os.getcwd())):
            if os.path.isdir(name):
                base_base_dir_name = os.path.join(base_dir_name, disk_dir)
                #print name
                process_dir(base_base_dir_name, name, target_dir)
        os.chdir("..")
    os.chdir("..")

def main():
    # target dir
    target_dir = os.path.join(os.getcwd(), "all-sorted")
    # both two source directories are organized differently
    process_base_dir_1("burn", target_dir)
    process_base_dir_1("on_cd", target_dir)
    process_base_dir_2("on_mp3_cd", target_dir)
    print "\nfinished."
    

if __name__ == "__main__":
    main()
