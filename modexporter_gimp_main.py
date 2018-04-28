import sys
import os.path
import multiprocessing
import subprocess
import time
import glob
import os
from shutil import copyfile

from os import listdir
from os.path import isfile, join

# 1. recurse through topdir / subdirs
# 2. for each subdir, create file/job pools + recurse through child subdirs
# 3. use pool to spawn 1 job per CPU core
# 4. check subdir path for each job to direct to appropriate script:
# a. if subdir == */textures/lowres/ then use lowres script for all child files/subdirs
# b. if subdir == */textures/menus/icons/ then use resize_icons script for all child files/subdirs
# c. else use convert_to_dds for child files/subdirs script
# d. for each script, handle normal maps based on subdir type


if (os.environ.get("GIMPEXE") is not None):
    gimpPath = os.environ["GIMPEXE"]
else:
    gimpPath = "C:/Program Files/GIMP 2/bin/gimp-console-2.8.exe"
if os.path.exists(gimpPath) == False:
	print "==================="
	print "ERROR: GIMP was not found. Please set the GIMPEXE variable to the path of your blender executable."
	print "==================="
	raw_input("Press ENTER to quit.")
	quit(-1)
if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
error_filename = outputRoot + "Oblivion.output/gimp_log.txt"
output_dir = outputRoot + "Oblivion.output/data/textures/"
job_pool = list()
try:
    CPU_COUNT = multiprocessing.cpu_count()
except NotImplementedError:
    CPU_COUNT = 1

def debug_print(err_string):
    global error_filename
    print err_string
    with open(error_filename, "a") as error_file:
        error_file.write(err_string + "\n")
        error_file.close()



# recurse_subdirs() is designed to traverse all files & subdirs to generate job_pool
# processing of job_pool should only occur after recurse_subdirs() completes.
# subdir must always end with "/" delimiter
def recurse_subdirs(subdir=""):
    global output_dir
    global job_pool    
    if (subdir == ""):
        subdir = output_dir
    if os.path.exists(subdir):
        #debug_print("DEBUG: searching subdir: " + subdir + "...")
        for filename in os.listdir(subdir):
            if os.path.isdir(subdir + filename):
                # recurse down and do check below
                recurse_subdirs(subdir + filename + "/")
                continue
            # if filename is supported, add fullpath to job pool
            if (".tga" in filename.lower() or ".dds" in filename.lower()):
                job_pool.append(subdir + filename)



def perform_job_old(in_file):
    global gimpPath
    # analyze in_file to decide which script to use
    # 1. convert to dds, 2. upsize icons, 3. downsize lowres, 4. fix mgso_normalmap
    # 2. upsize icons
    if ("/menus/icons/" in in_file.lower()):
        scriptfile = "modexporter_gimp_icons"
    # 3. downsize lowres
    elif ("/lowres/" in in_file.lower()):
        scriptfile = "modexporter_gimp_lowres"
    # 4. fix mgso_normalmap
    elif ("_n.dds" in in_file.lower()):
        scriptfile = "modexporter_gimp_nmaps_fix"
    # 1. convert to dds (default)
    else:
        scriptfile = "modexporter_gimp_todds"
    ## LOAD GIMP HERE....
    #print "==================="
    #debug_print("\n================\nstarting gimp: [" + scriptfile + "] " + in_file)
    #print "==================="
    #raw_input("DEBUG: PRESS ENTER TO BEGIN")
    #bootstrap = "gimp.message('Hello, world')"
    #bootstrap = str("import sys;sys.path=['.']+sys.path;import " + scriptfile + ";gimp.message(str(sys.path))")
    #bootstrap = "import sys;sys.path=['.']+sys.path;import " + scriptfile + ";" + scriptfile + ".run('test')"
    bootstrap = "import sys;sys.path=['.']+sys.path;import " + scriptfile + ";" + scriptfile + ".run('" + in_file + "')"
    #debug_print("bootstrap=" + bootstrap)
    #bootstrap = "import sys;sys.path=['.']+sys.path;gimp.message(str(sys.path));import " + scriptfile + ";" + scriptfile + ".run('" + in_file + "');pdb.gimp_quit(0)"
    #print "====GIMP script bootstrap:=======\n" + bootstrap + "\n================\n"
    resultcode = subprocess.call([gimpPath, \
                          "-idf", "--batch-interpreter=python-fu-eval", \
#                         "-b", "\"import sys;sys.path=['.']+sys.path;import " + scriptfile + ";modexporter_gimp.run(\"" + in_file + "\")\"", \
#                        "-b", "\"import sys;sys.path=['.']+sys.path;import modexporter_gimp;modexporter_gimp.run(\"" + in_file + "\")\"", \
#                          "-b", "\"import sys;sys.path=['.']+sys.path;import " + scriptfile + ";" + scriptfile + ".run()\"", \
#                          "-b", "(pdb.gimp_quit(0))"])
#                          "-b", "\import sys;sys.path=['.']+sys.path;import " + scriptfile + ";" + scriptfile + ".run('" + in_file + "')\""])
                          "-b", bootstrap])
    if (resultcode != 0):
        #print "ERROR: failed with resultcode=(" + str(resultcode) + ")"
        # log error and continue
        debug_print(in_file + " failed: resultcode=(" + str(resultcode) + ")\n")
        return -1
    else:
        debug_print(in_file + " success.\n")
        return 0



def perform_job_new(joblist):
    scriptfile = "modexporter_gimp_job"
    bootstrap = "import sys;sys.path=['.']+sys.path;import " + scriptfile + ";" + scriptfile + ".run('" + joblist + "')"
    #debug_print("bootstrap=" + bootstrap)
    #print "====GIMP script bootstrap:=======\n" + bootstrap + "\n================\n"
    resultcode = subprocess.call([gimpPath, \
                          "-idf", "--batch-interpreter=python-fu-eval", \
                          "-b", bootstrap])
    os.remove(joblist)
    if (resultcode != 0):
        #print "ERROR: failed with resultcode=(" + str(resultcode) + ")"
        # log error and continue
        debug_print(joblist + " failed: resultcode=(" + str(resultcode) + ")\n")
        return -1
    else:
        debug_print(joblist + " success.\n")
        return 0  


def main():
    global error_filename
    global job_pool
    # check for prior run
    if (os.path.exists(error_filename) == True):
        print "Existing \\Oblivion.output\\gimp_log.txt was detected.  Please delete or rename this file if you are sure you want to rerun this sript and modify your textures."
        raw_input()
        os.remove(error_filename)
        #return(-1)
    #raw_input("CPUS=[" + str(CPU_COUNT) + "] PRESS ENTOER TO CONTINUE")
    
    # prepare job_pool
    recurse_subdirs()
    #raw_input("JOB SIZE=[" + str(len(job_pool)) + "]  PRESS ENTER TO CONTINUE")

##    # DEBUG: test job
##    for j in job_pool:
##        if ("menus/icons/" in j.lower()):
##            perform_job(j)
##            raw_input("PRESS ENTER TO CONTINUE")

    # output joblists
    for templist in glob.glob("gimp_templist*.job"):
        os.remove(templist)
    for list_index in range(0,CPU_COUNT,1):
        joblist = "gimp_templist" + str(list_index) + ".job"
        chunksize = int(len(job_pool) / CPU_COUNT)
        startcount = int(chunksize * list_index)
        stopcount = int(startcount + chunksize)
        if list_index == CPU_COUNT-1:
            stopcount = len(job_pool)
        #print "DEBUG: startcount=" + str(startcount) + "; stopcount=" + str(stopcount) + "; job_pool=" + str(len(job_pool)) + "; chunksize=" + str(chunksize)
        with open(joblist, "w") as temp_list:
            for jobname in job_pool[startcount:stopcount]:
                temp_list.write(jobname + "\n")
            temp_list.close()
    # test joblists
    #for joblist in glob.glob("gimp_templist*.job"):
    #    perform_job_new(joblist)


    # process job_pool
    pool = multiprocessing.Pool(processes=CPU_COUNT)
    joblists = glob.glob("gimp_templist*.job")
    result = pool.map_async(perform_job_new, joblists)
    try:
        result.wait(timeout=99999999)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        quit(-1)
    raw_input("JOBS completed.")
    return(0)


##    # process job_pool
##    pool = multiprocessing.Pool(processes=CPU_COUNT)
###    pool = multiprocessing.Pool(processes=1)
##    result = pool.map_async(perform_job, job_pool)
##    try:
##        result.wait(timeout=99999999)
##        pool.close()
##        pool.join()
##    except KeyboardInterrupt:
##        quit(-1)
##    raw_input("JOBS completed.")
##    return(0)



if __name__ == "__main__":
    main()
