import sys
import os.path
import subprocess
import time
import glob

from os import listdir
from os.path import isfile, join

if (os.environ.get("BLENDEREXE") is not None):
    blenderPath = os.environ["BLENDEREXE"]
else:
    blenderPath = "C:/Program Files (x86)/Blender Foundation/Blender/blender.exe"
if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
print "DEBUG: outputRoot = " + outputRoot + ", blenderPath = " + blenderPath
error_filename = outputRoot + "Oblivion.output/error_list.txt"
output_path = outputRoot + "Oblivion.output/Data/Meshes/"
outlist_path = outputRoot + "Oblivion.output/jobs/"
blenderFilename = "empty.blend"

def error_list(err_string):
    with open(error_filename, "a") as error_file:
        error_file.write(err_string + "\n")

def select_job_file():
    global jobname
    global input_files
    global fullres_collisions
    #set up input files
    fullres_collisions = False
    ## process regular list
    file_found = False
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
            if (os.path.exists(filename) == False) or ("morro\\e\\" in filename) or ("morro/e/" in filename):
                continue
            else:
                input_files.append(filename)
        outlist_file.close()
    else:
        return -1

def perform_job():
    global jobname
    global input_files
    global fullres_collisions
    global blenderPath
    #arguments = sys.argv
    #blenderpath = arguments[len(arguments)-1]
    for in_file in input_files:
        if ("_clothing_" in jobname) and ("ugnd.nif" not in in_file.lower()):
            conversion_script = "modexporter_convert_clothing.py"
        else:
            conversion_script = "modexporter_blender_convert_one.py"
        ## LOAD BLENDER HERE....
        print "==================="
        print "starting blender..." + in_file
        print "==================="
        #raw_input("DEBUG: PRESS ENTER TO BEGIN")
        if ("_far.nif" in in_file):
            rc = subprocess.call([blenderPath, blenderFilename, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
        else:
            rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
        if (rc != 0):
            print "Error launching blender: retrying with gui enabled..."
            #raw_input("Press Enter to continue.")
            rc = subprocess.call([blenderPath, blenderFilename, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", in_file,"--fullres_collisions", str(int(fullres_collisions))])
            if (rc != 0):
                print "Unable to launch blender, logging error and skipping file..."
                # log error and continue
                error_list(in_file + " (launch error) could not start blender.")
                #continue

            
def complete_job():
    global jobname
    global input_files
    # remark jobfile as done
    if (jobname == ""):
        return -1
    if os.path.exists(jobname):
        if os.path.exists(jobname+".done"):
            os.remove(jobname+".done")
        os.rename(jobname, jobname+".done")
        os.remove(jobname+".lock")
    #print script complete statements.
    print ""
    print "job completed: " + jobname

def get_next_job():
    global jobname
    global input_files
    input_files = []
    jobname = ""
    if (select_job_file() == -1):
        return -1
    perform_job()
    complete_job()

def count_jobs_and_locks():
    global num_jobs
    global num_locks
    num_jobs = 0
    num_locks = 0
    allJobs = glob.glob(outlist_path + "*.job")
    for job in allJobs:
        num_jobs += 1
    allLocks = glob.glob(outlist_path + "*.lock")
    for lock in allLocks:
        num_locks += 1

def issue_lock_warning():
    global num_jobs
    global num_locks
    print "--------------------------------"
    print "(" + str(num_locks) + ") Lock file(s) detected!"
    print ""
    print "If you recently crashed, then please run the"
    print "cleanup script."
    print ""
    print "Unless you know what you are doing, press CTRL+C"
    print "now and quit!  Continuing will spawn a concurrent"
    print "job session.  Proceed with caution!"
    print ""
    print "--------------------------------"
    try:
        raw_input("Press CTRL+C to quit or ENTER to continue.")
    except KeyboardInterrupt:
        quit()

def print_jobs_info():
    global num_jobs
    global num_locks
    print "--------------------------------"
    print ""
    print "Total available jobs found = " + str(num_jobs-num_locks)
    print "Press ENTER to start processing jobs."
    print ""
    print "--------------------------------"
    raw_input("")

def print_jobs_complete_quit():
    print "--------------------------------"
    print ""
    print "Jobs completed. Press ENTER to exit script."
    print ""
    print "--------------------------------"
    raw_input("")
    quit()

# main
def main():
    global num_jobs
    global num_locks
    # count jobs
    # count locks
    count_jobs_and_locks()
    # issue lock warning
    if (num_locks > 0):
        issue_lock_warning()
    # print jobs info
    if (num_jobs > 0):
        print_jobs_info()
    else:
        print_jobs_complete_quit()
    # get next job
    while (num_jobs > 0) and (num_locks < num_jobs):
        try:
            print "DEBUG: counting... jobs left = " + str(num_jobs) + ", locks = " + str(num_locks)
            count_jobs_and_locks()
            get_next_job()
        except KeyboardInterrupt:
            try:
                raw_input("Conversion interrupted by user. Press CTRL+C again to quit or ENTER to continue with next file.")
            except KeyboardInterrupt:
                quit()
    print_jobs_complete_quit()



if __name__ == "__main__":
    main()
