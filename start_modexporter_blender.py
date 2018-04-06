import sys
import os.path
import subprocess
import time
import glob

from os import listdir
from os.path import isfile, join

def error_list(err_string):
    with open("C:/Oblivion.output/error_list.txt", "a") as error_file:
        error_file.write(err_string + "\n")

#set up input files
input_files = list()
output_path = "C:/Oblivion.output/Data/Meshes/"
fullres_collisions = False
## process regular list
file_found = False
outlist_path = "c:/Oblivion.output/jobs/"

alljobs = glob.glob(outlist_path + "*.job")
for jobname in alljobs:
    if os.path.exists(jobname+".lock"):
        continue
    else:
        try:
            jobname_lock = open(jobname+".lock", "w")
        except:
            continue
    jobname_lock.close()
    file_found = True
    break;

if (file_found == True):
    if ("_fullres_collision_" in jobname):
        # process as fullres
        fullres_collisions = True
    outlist_file = open(jobname, "r")
    print "Job file selected: " + jobname
    for line in outlist_file: 
        # remove eol char
        filename = output_path + line[:len(line)-1]
        if (os.path.exists(filename) == False) or ("morro\\e\\" in filename):
            continue
        else:
            input_files.append(filename)
    outlist_file.close()

arguments = sys.argv
blenderpath = arguments[len(arguments)-1]
#blenderpath = "C:/Program Files (x86)/Blender Foundation/Blender/blender.exe"
for in_file in input_files:
    if ("_clothing_" in jobname) and ("ugnd.nif" not in in_file.lower()):
        conversion_script = "modexporter_convert_clothing.py"
    else:
        conversion_script = "modexporter_blender_convert_one.py"

    ## LOAD BLENDER HERE....
    print "==================="
    print "starting blender..."
    print "==================="
    if ("_far.nif" in in_file):
        rc = subprocess.call([blenderpath, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
    else:
        rc = subprocess.call([blenderpath, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
    if (rc != 0):
        print "Error launching blender: retrying with gui enabled..."
        #raw_input("Press Enter to continue.")
        rc = subprocess.call([blenderpath, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
        if (rc != 0):
            print "Unable to launch blender, logging error and skipping file..."
            # log error and continue
            error_list(in_file + " (launch error) could not start blender.")
            #continue
##        else:
##            print "successful launch on second attempt."
##    else:
##            print "successful launch on first attempt."
            

# remark jobfile as done
if os.path.exists(jobname):
    if os.path.exists(jobname+".done"):
        os.remove(jobname+".done")
    os.rename(jobname, jobname+".done")
    os.remove(jobname+".lock")
#print script complete statements.
print ""
print "job completed: " + jobname
