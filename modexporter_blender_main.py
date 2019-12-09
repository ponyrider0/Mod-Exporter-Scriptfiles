import sys
import os
import os.path
import multiprocessing
import subprocess
import Queue
import time
import glob

from os import listdir
from os.path import isfile, join

from pyffi.formats.nif import NifFormat
import pyffi.spells.nif.modify
import pyffi.spells.nif.fix
import pyffi.spells.nif.optimize
import pyffi.spells.nif


if (os.environ.get("BLENDEREXE") is not None):
    blenderPath = os.environ["BLENDEREXE"]
else:
    blenderPath = "C:/Blender/blender.exe"

#print "==============DEBUG=============="
#print ""
#print "DEBUG: BLENDEREXE = " + os.environ["BLENDEREXE"]
#print "DEBUG: BLENDERPATH = " + blenderPath
#print ""
#print "==============DEBUG=============="
#raw_input("Press ENTER to continue.")

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

nifConvPath = "NIF_Conv.exe"


def error_list(err_string):
    print(err_string)
    writemode = 'a'
    if not os.path.exists(error_filename):
        writemode = 'w'
    with open(error_filename, writemode) as error_file:
#    with open(error_filename, "a") as error_file:
        error_file.write(err_string + "\n")


class SpellDelMaterialProperties(pyffi.spells.nif.modify._SpellDelBranchClasses):
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiMaterialProperty,)
    SPELLNAME = "delmaterialprop"


def postprocess_nifdata(x):
##    pyffi.spells.nif.optimize.SpellOptimizeGeometry(data=x).recurse()
###    toaster = pyffi.spells.nif.NifToaster()
###    toaster.options["arg"] = -0.1
###    spell = pyffi.spells.nif.optimize.SpellReduceGeometry(data=x, toaster=toaster)
###    spell.recurse()
#    delBranches = pyffi.spells.nif.modify._SpellDelBranchClasses(data=x)
#    delBranches.BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiMaterialProperty,)
#    delBranches.recurse()
#    pyffi.spells.nif.optimize.SpellCleanRefLists(data=x).recurse()

#    SpellDelMaterialProperties(data=x).recurse()
    delBranches = pyffi.spells.nif.modify._SpellDelBranchClasses(data=x)
    delBranches.BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiMaterialProperty,)
    delBranches.recurse()
    pyffi.spells.nif.fix.SpellDelUnusedRoots(data=x).recurse()
    pyffi.spells.nif.optimize.SpellCleanRefLists(data=x).recurse()
#    pyffi.spells.nif.fix.SpellDetachHavokTriStripsData(data=x).recurse()
#    pyffi.spells.nif.fix.SpellFixTexturePath(data=x).recurse()
#    pyffi.spells.nif.fix.SpellFixBhkSubShapes(data=x).recurse()
#    pyffi.spells.nif.fix.SpellFixEmptySkeletonRoots(data=x).recurse()
    pyffi.spells.nif.optimize.SpellOptimizeGeometry(data=x).recurse()
    pyffi.spells.nif.optimize.SpellOptimizeCollisionBox(data=x).recurse()
    pyffi.spells.nif.optimize.SpellOptimizeCollisionGeometry(data=x).recurse()
    pyffi.spells.nif.optimize.SpellMergeDuplicates(data=x).recurse()
    
    print "DEBUG: postproccessed!"
    return x

def postprocessNif(filename):
    input_stream = open(filename, "rb")
    nifdata = NifFormat.Data()
    try:
        nifdata.read(input_stream)
    except Exception as e:
        # nif-read error, something wrong with NIF, delete...
        input_stream.close()
        os.remove(filename)
        s = "\n\npostprocessNif(): ERROR reading(" + filename + "); deleting file."
#        print(s)
        error_list(s)
        return -1
    input_stream.close()
    try:
        nifdata = postprocess_nifdata(nifdata)
        output_stream = open(filename, "wb")
        nifdata.write(output_stream)
        output_stream.close()
        print "PostProcessing(" + filename + ") complete."
    except Exception as e:
        s = "\n\nERROR post-processing(" + filename + ")..."
#        print(s)
        error_list(s)
    return 0


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
        for raw_line in outlist_file: 
            # remove eol char
            args_list = []
            args_list = raw_line.rstrip("\r\n").split(":")
#            print "DEBUG: raw_line = %s" % (raw_line)
#            print "DEBUG: args_list (#%d) = %s" % (len(args_list), args_list[0])
            line = args_list[0]
            in_filename = input_path + line.rstrip("\r\n")
            out_filename = output_path + line.rstrip("\r\n")
            #print "DEBUG: looking for: " + filename + "..."
#            if (os.path.exists(in_filename) == False) or ("morro/e/" in in_filename):
            if ("morro/e/" in in_filename):
                #print "DEBUG: file not found, skipping."
                continue
            elif (os.path.exists(out_filename) == True):
                continue
            else:
                #print "DEBUG: input file found, adding to queue for processing."
#                args_list[0] = out_filename
                input_files.append(args_list)
        outlist_file.close()
        if (input_files == []):
            print "WARNING: no valid files were found in jobfile:\n" + jobname
            #raw_input("DEBUG: Press CTRL+C to quit or ENTER to continue with next file.\n")
    else:
        print "No jobs found. DEBUG: search was for: " + outlist_path + "*.job"
        return -1



def jobthread_clothing(filename_args):
    global fullres_collisions
    global blenderPath

    filename = filename_args[0]
    orig_file = ""
    cmdflags = ""
    if len(filename_args) > 1:
        orig_file = filename_args[1]
    if len(filename_args) > 2:
        cmdflags = filename_args[2]

    if ("ugnd.nif" in filename.lower()):
        conversion_script = "modexporter_blender_generic.py"
    else:
        conversion_script = "modexporter_blender_clothing.py"
    #print "starting blender..." + filename
    #print "DEBUG: blenderPath=" + blenderPath + "; script=" + conversion_script + "; fullres_collisions=" + str(int(fullres_collisions))
    rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", output_path+filename,"--fullres_collisions", str(int(fullres_collisions))])
    if (rc != 0):
        rc = subprocess.call([blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", output_path+filename,"--fullres_collisions", str(int(fullres_collisions))])
        if (rc != 0):
            # log error and continue
            error_list(filename + " (launch error) could not start blender.")
            return -1

    if os.path.exists(output_path+filename):
        rc = postprocessNif(output_path+filename)
    else:
        rc = -1
        error_list("ERROR: blender_clothing script failed to produce output: " + output_path + filename)
#    rc = postprocessNif(output_path+filename)
    return rc


def jobthread_generic(filename_args):
    global fullres_collisions
    global blenderPath

    filename = filename_args[0]
    orig_file = ""
    cmdflags = ""
    if len(filename_args) > 1:
        orig_file = filename_args[1]
    if len(filename_args) > 2:
        cmdflags = filename_args[2]
#    print "DEBUG: args_list (#%d) = filename=%s, orig_file=%s, cmdflags=%s" % (len(filename_args), filename, orig_file, cmdflags)
    
    conversion_script = "modexporter_blender_generic.py"
    #print "starting blender..." + filename
    #print "DEBUG: blenderPath=" + blenderPath + "; script=" + conversion_script + "; fullres_collisions=" + str(int(fullres_collisions))
    if ("_far.nif" in filename):
        return -1
    else:
        nifCall = []
        nifCall.append(nifConvPath)
        nifCall.append(orig_file)
        if cmdflags is not "" and cmdflags is not " ":
            for flags in cmdflags.split(" "):
                if flags is not "" and flags is not " ":
                    nifCall.append(flags)
        else:
            cmdflags = None
        nifCall.append("-d")
        nifCall.append(filename.replace("/", "\\"))
        # attempt #1
        commandLineString = ""
        for s in nifCall:
            commandLineString = commandLineString + s + " "
        error_list("DEBUG: attempt#1, (" + filename + ") attempting to launch NIF_conv.exe...\ncommand=" + commandLineString)
        rc = subprocess.call(nifCall)
        if os.path.exists(output_path+filename):
            rc = postprocessNif(output_path+filename)
        else:
            rc = -1
            error_list("ERROR: NIF_Conv.exe failed to produce output: " + output_path + filename)
    if (rc != 0):
        if ("_far.nif" in filename):
            return -1
        else:
            blenderCall = [blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", output_path+filename,"--fullres_collisions", str(int(fullres_collisions))]
            commandLineString = ""
            for s in blenderCall:
                commandLineString = commandLineString + s + " "
            error_list("DEBUG: attempt#2, (" + filename + ") attempting to launch Blender fallback...\ncommand=" + commandLineString)
            # attempt #2
            rc = subprocess.call(blenderCall)
        if (rc != 0):
            if ("_far.nif" in filename):
                return -1
            else:
                blenderCall = [blenderPath, blenderFilename, "-b", "-p", "0", "0", "1", "1", "-P", conversion_script, "--", output_path+filename,"--fullres_collisions", str(int(fullres_collisions))]
                commandLineString = ""
                for s in blenderCall:
                    commandLineString = commandLineString + s + " "
                error_list("DEBUG: attempt#3, (" + filename + ") attempting to launch Blender fallback...\ncommand=" + commandLineString)
                #attempt #3
                rc = subprocess.call(blenderCall)
            if (rc != 0):
                # log error and continue
                error_list(filename + " (launch error) could not start blender.")
                return -1
        if os.path.exists(output_path+filename):
            rc = postprocessNif(output_path+filename)
        else:
            rc = -1
            error_list("ERROR: blender fallback script failed to produce output: " + output_path + filename)
#        rc = postprocessNif(output_path+filename)
    return rc


def jobthread_clothing_safe(args):
    filename_args, mqueue = args[0], args[1]
    try:
        jobthread_clothing(filename_args)
    except Exception as e:
        mqueue.put(e)

def jobthread_generic_safe(args):
    filename_args, mqueue = args[0], args[1]
    try:
        jobthread_generic(filename_args)
    except Exception as e:
        mqueue.put(e)


def spawn_job_threads(jobname):
    global CPU_COUNT
    global input_files
    if (len(input_files) == 0):
        return 0
    #print "CPUS=[" + str(CPU_COUNT) + "]"
    #raw_input("JOB SIZE=[" + str(len(input_files)) + "]  PRESS ENTER TO CONTINUE")
    manager = multiprocessing.Manager()
    mqueue = manager.Queue()
    pool = multiprocessing.Pool(processes=CPU_COUNT)
#    pool = multiprocessing.Pool(processes=1)
    if ("_clothing_" in jobname):
        map_async_result = pool.map_async(jobthread_clothing_safe, [(x, mqueue) for x in input_files])
    else:
        map_async_result = pool.map_async(jobthread_generic_safe, [(x, mqueue) for x in input_files])

##    # non-blocking job processing
##    while not map_async_result.ready() or mqueue.qsize() > 0:
##        try:
##            mqueue_result = mqueue.get_nowait()
##        except Queue.Empty:
##            time.sleep(1)
##            continue
##        if isinstance(mqueue_result, Exception):
##            raise mqueue_result

    # block until all jobs processed
    try:
        map_async_result.wait(timeout=99999999)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print "Keyboard interrupt detected."
#        quit(-1)

    # complete processing any remaining mqueue results
    while True:
        try:
            mqueue_result = mqueue.get_nowait()
        except Queue.Empty:
            break
        if isinstance(mqueue_result, Exception):
            raise mqueue_result
        
    return 0


            
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
    if (spawn_job_threads(jobname) == -1):
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
    print "Total available jobs found = " + str(num_jobs-num_locks)
    print "--------------------------------"
#    raw_input("")

def print_jobs_complete_quit():
    print "--------------------------------"
    print "Jobs completed."
    print "--------------------------------"
#    raw_input("")
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
