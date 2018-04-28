import sys
import os.path
import multiprocessing
import subprocess
import time
import glob

from os import listdir
from os.path import isfile, join

if (os.environ.get("BLENDEREXE") is not None):
    blenderPath = os.environ["BLENDEREXE"]
else:
    blenderPath = "C:/Program Files (x86)/Blender Foundation/Blender/blender.exe"
if os.path.exists(blenderPath) == False:
	print "==================="
	print "ERROR: Blender was not found. Please set the BLENDEREXE variable to the path of your blender executable."
	print "==================="
	raw_input("Press ENTER to quit.")
	quit(-1)
if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
#print "DEBUG: outputRoot = " + outputRoot + ", blenderPath = " + blenderPath
error_filename = outputRoot + "Oblivion.output/error_list.txt"
input_path = outputRoot + "Oblivion.output/temp/Meshes/"
output_path = outputRoot + "Oblivion.output/Data/Meshes/"
outlist_path = outputRoot + "Oblivion.output/jobs/"
blenderFilename = "empty.blend"
try:
    CPU_COUNT = multiprocessing.cpu_count()
except NotImplementedError:
    CPU_COUNT = 1
fullres_collisions = True

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
            in_filename = input_path + line.rstrip("\r\n")
            out_filename = output_path + line.rstrip("\r\n")
            #print "DEBUG: looking for: " + filename + "..."
            if (os.path.exists(in_filename) == False) or ("morro/e/" in in_filename):
                #print "DEBUG: file not found, skipping."
                continue
            elif (os.path.exists(out_filename) == True):
                continue
            else:
                #print "DEBUG: input file found, adding to queue for processing."
                input_files.append(out_filename)
        outlist_file.close()
        if (input_files == []):
            print "WARNING: no valid files were found in jobfile:\n" + jobname
            #raw_input("DEBUG: Press CTRL+C to quit or ENTER to continue with next file.\n")
    else:
        print "No jobs found. DEBUG: search was for: " + outlist_path + "*.job"
        return -1



def perform_job_new_clothing(filename):
    global fullres_collisions
    global blenderPath
    if ("ugnd.nif" in filename.lower()):
        conversion_script = "modexporter_blender_generic.py"
    else:
        conversion_script = "modexporter_blender_clothing.py"
    #print "starting blender..." + filename
    #print "DEBUG: blenderPath=" + blenderPath + "; script=" + conversion_script + "; fullres_collisions=" + str(int(fullres_collisions))    
    rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
    if (rc != 0):
        rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
        if (rc != 0):
            # log error and continue
            error_list(filename + " (launch error) could not start blender.")
            return -1
    return 0

def perform_job_new_generic(filename):
    global fullres_collisions
    global blenderPath
    conversion_script = "modexporter_blender_generic.py"
    #print "starting blender..." + filename
    #print "DEBUG: blenderPath=" + blenderPath + "; script=" + conversion_script + "; fullres_collisions=" + str(int(fullres_collisions))    
    if ("_far.nif" in filename):
        rc = subprocess.call([blenderPath, blenderFilename, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
    else:
        rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
    if (rc != 0):
        if ("_far.nif" in filename):
            rc = subprocess.call([blenderPath, blenderFilename, "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
        else:
            rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", filename,"--fullres_collisions", str(int(fullres_collisions))])
        if (rc != 0):
            # log error and continue
            error_list(filename + " (launch error) could not start blender.")
            return -1
    return 0

def perform_job_new(jobname):
    global CPU_COUNT
    global input_files
    if (len(input_files) == 0):
        return 0
    #print "CPUS=[" + str(CPU_COUNT) + "]"
    #raw_input("JOB SIZE=[" + str(len(input_files)) + "]  PRESS ENTER TO CONTINUE")
    pool = multiprocessing.Pool(processes=CPU_COUNT)
#    pool = multiprocessing.Pool(processes=1)
    if ("_clothing_" in jobname):
        result = pool.map_async(perform_job_new_clothing, input_files)
    else:
        result = pool.map_async(perform_job_new_generic, input_files)
    try:
        result.wait(timeout=99999999)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        return -1
    return 0

def perform_job_old():
    global jobname
    global input_files
    global fullres_collisions
    global blenderPath
    for in_file in input_files:
        if ("_clothing_" in jobname) and ("ugnd.nif" not in in_file.lower()):
            conversion_script = "modexporter_blender_clothing.py"
        else:
            conversion_script = "modexporter_blender_generic.py"
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
                return -1

            
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

def process_next_job():
    global jobname
    global input_files
    input_files = []
    jobname = ""
    if (select_job_file() == -1):
        return 0
    if (perform_job_new(jobname) == -1):
        print "DEBUG: error occured while processing job. Please see Oblivion.output\error_list.txt for more information."
        raw_input("Press ENTER to try to continue with next file or CTRL+C to quit.")
        return -1
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
        raw_input("Press CTRL+C to quit or ENTER to continue.\n")
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
            #print "DEBUG: counting... jobs left = " + str(num_jobs) + ", locks = " + str(num_locks)
            count_jobs_and_locks()
            if (process_next_job() == -1):
                print "==========================================="
                print ""
                print "ERROR: "
                print "An error occured while processing jobs. Make sure your have full file permissions to Oblivion.output and Oblivion.output\jobs folders."
                print ""
                print "==========================================="
                raw_input("Press ENTER to quit.\n")
                quit()
        except KeyboardInterrupt:
            try:
                raw_input("\nConversion interrupted by user. Press CTRL+C again to quit or ENTER to continue with next file.\n")
            except KeyboardInterrupt:
                quit()
    print_jobs_complete_quit()



if __name__ == "__main__":
    main()
