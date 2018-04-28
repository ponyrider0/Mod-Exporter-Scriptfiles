import sys
import os
import pdb
from gimpfu import *

sys.path = ['.'] + sys.path
import modexporter_gimp_icons
import modexporter_gimp_nmaps_fix
import modexporter_gimp_dds
import modexporter_gimp_lowres

log_messages = False
print_messages = True
if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
output_dir = outputRoot + "Oblivion.output/data/textures/"
error_filename = outputRoot + "Oblivion.output/gimp_log.txt"

def debug_output(message):
    if (print_messages == True):
        gimp.message(message)
    if (log_messages == True):
        with open(error_filename, "a") as error_file:
            error_file.write(message + "\n")
            error_file.close()



def run(joblist):
    debug_output("processing joblist: " + joblist)
    job_file = open(joblist, "r")
    for line in job_file:
        filename = line.rstrip("\r\n")
        debug_output(filename)
        if (os.path.exists(filename) == False):
            continue
        # use one of 4 scripts
        if ("/menus/icons/" in filename.lower()):
            modexporter_gimp_icons.run(filename)
        # 3. downsize lowres
        elif ("/lowres/" in filename.lower()):
            modexporter_gimp_lowres.run(filename)
        # 4. fix mgso_normalmap
        elif ("_n.dds" in filename.lower()):
            modexporter_gimp_nmaps_fix.run(filename)
        # 1. convert to dds (default)
        else:
            modexporter_gimp_dds.run(filename)
    job_file.close()
    pdb.gimp_quit(0)



if __name__ == "__main__":
    debug_output("This is a GIMP utility script that is designed to only be called by another script.  Exiting.")

    
