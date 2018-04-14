import Blender
import bpy
import sys
import gc
#import Mathutils
import math
import os.path

if (os.environ.get("HOME") is not None):
    sys.path.append(os.environ["HOME"])

from import_nif_con import NifImport
from export_nif_con import NifExport
from nif_common_con import NifConfig

if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
error_filename = outputRoot + "Oblivion.output/error_list.txt"

def error_list(err_string):
    with open(error_filename, "a") as error_file:
        error_file.write(err_string + "\n")

argv = sys.argv
argv = argv[argv.index("--") + 1:]
out_file = argv[0]
# Assuming "/data/meshes" in path, redirect to /Temp/Meshes
in_file = out_file.lower().replace("/data/meshes/", "/temp/meshes/")
if os.path.exists(in_file) == False:
    print "Input file not found! skipping file..."
    Blender.Quit()
if os.path.exists(out_file) == True:
    print "Output file already exists, skipping file..."
    Blender.Quit()
Blender.Set("texturesdir", outputRoot + "Oblivion.output/Data/Textures/")

print "==========="
print "Importing file: " + in_file
print "==========="
config = dict(**NifConfig.DEFAULTS)
config["IMPORT_FILE"] = in_file
config["IMPORT_SKELETON"] = 0
NifImport(**config)

# try to detect Better Clothes skeleton
altskeleton = False
isRobe = False
try:
    arm = bpy.data.armatures["Bip01"]
except KeyError, e:
    print "ERROR reading armature[Bip01]. Niffile:[" + in_file + "] may already be converted. Quiting..."
    Blender.Quit()
bone = arm.bones["Bip01 Pelvis"]
if (abs(bone.head["ARMATURESPACE"][0]) > 0.0001):
    altskeleton = True
    #raw_input("Bad Skeleton detected")
elif (abs(bone.head["ARMATURESPACE"][2]) > 0.1):
    isRobe = True
    #raw_input("Robe detected")

#unparent meshes
for ob in bpy.data.objects:
    ob.clrParent(2)

for ob in bpy.data.objects:
    if ob.type == "Armature":
        bpy.data.scenes.active.objects.unlink(ob)

for ob in bpy.data.objects:
    #ob.select(False)
    for mod in ob.modifiers:
        ob.modifiers.remove(mod)
    if ob.type == "Mesh":
        for mat in ob.getData(mesh=1).materials:
            mat.name = "clothes"

ob_selection = list()
for ob in bpy.data.objects:
    if ob.type == "Mesh" or ob.type == "Empty":
        ob_selection.append(ob)
        if (altskeleton == True):
            ob.setLocation(ob.loc[0], ob.loc[1]+0.33, ob.loc[2])
        elif (isRobe == True):
            ob.setEuler(0, 0, math.pi)
            ob.setLocation(ob.loc[0], ob.loc[1]+0.12, ob.loc[2]+1.1)
        else:
            ob.setLocation(ob.loc[0], ob.loc[1]+0.12, ob.loc[2])                        

print "==========="
print "Importing skeleton"
print "==========="
if (altskeleton == True):
    config["IMPORT_FILE"] = "export_skeleton_b.nif"
else:
    config["IMPORT_FILE"] = "export_skeleton_a.nif"        
config["IMPORT_SKELETON"] = 1
config["EXPORT_OBJECTS"] = ob_selection
NifImport(**config)

if (altskeleton == True):
    print "Resetting skeleton"
    ob_selection = []
    for ob in bpy.data.objects:
        if ob.type == "Mesh":
            ob_selection.append(ob)
    root = bpy.data.objects["Scene Root"]
    root.makeParentBone(ob_selection, "Bip01.00")

ob_selection = []
for ob in bpy.data.scenes.active.objects:
    if ob.type == "Mesh" or ob.type == "Empty":
        ob_selection.append(ob)
    #ob.select(True)

folderPath = os.path.dirname(out_file)
try:
    if os.path.exists(folderPath) == False:
        os.makedirs(folderPath)
except:
    print "Export ERROR: could not create destination directory: " + folderPath
    error_list(in_file + "Export ERROR: could not create destination directory: " + folderPath)
    Blender.Quit()

#out_file = in_file[:len(in_file)-4] + "_tes4.nif"
print "==========="
print "Exporting file..." + out_file
print "==========="
config["EXPORT_VERSION"] = 'Oblivion'
config["EXPORT_FILE"] = out_file
config["EXPORT_OBJECTS"] = ob_selection
config["EXPORT_ANIMATION"] = 1
config["EXPORT_FLATTENSKIN"] = True
NifExport(**config)

#raw_input("DEBUG: Press Enter to continue.")
Blender.Quit()
