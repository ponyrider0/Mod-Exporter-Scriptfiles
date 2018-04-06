import sys
import os.path
import subprocess
import time
import glob

from os import listdir
from os.path import isfile, join

def error_list(err_string):
    with open("error_list.txt", "a") as error_file:
        error_file.write(err_string + "\n")

def recurse_dir(dirname, search_term=""):
    if os.path.exists(dirname) == False:
        raw_input("Folder does not exist: " + dirname + "Press ENTER to quit.")
        quit()
    else:
        for filename in os.listdir(dirname):
            if os.path.isdir(dirname+"\\"+filename):
                recurse_dir(dirname +"\\"+ filename)
                continue
            if (search_term not in filename.lower()):
                continue
            try:
                print "Performing operation on: " + filename
                input_files.append(dirname+"\\"+filename)
            except:
                raw_input("Error trying to perform operation on: " + filename)
                continue

#set up input files
input_files = list()
argv = sys.argv
argv = argv[argv.index("--") + 1:]
blenderpath = argv[0]
niffolder = argv[1]
fullres_collisions = True

recurse_dir(niffolder, "_far.nif")

for in_file in input_files:
    conversion_script = "convert_mesh_folder_per_file.py"
    
    ## LOAD BLENDER HERE....
    print "==================="
    print "starting blender for: " + in_file
    print "==================="
    rc = subprocess.call([blenderpath, "-b", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions)), "--polyreduce_models", "0"])
    if (rc != 0):
        print "Error launching blender: retrying with gui enabled..."
        #raw_input("Press Enter to continue.")
        rc = subprocess.call([blenderpath, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions)), "--polyreduce_models", "0"])
        if (rc != 0):
            print "Unable to launch blender, logging error and skipping file..."
            # log error and continue
            error_list(in_file + " (launch error) could not start blender.")
            #continue
        else:
            print "successful launch on second attempt."
    else:
            print "successful launch on first attempt."
    #raw_input("Press Enter to continue.")

