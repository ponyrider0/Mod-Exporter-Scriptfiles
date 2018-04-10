import Blender
import bpy
import sys
import gc

if (os.environ.get("HOME") is not None):
    sys.path.append(os.environ["HOME"])

#import Mathutils
from import_nif_con import NifImport
from export_nif_con import NifExport
from nif_common_con import NifConfig
from nif_common_con import NifFormat

if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
error_filename = outputRoot + "Oblivion.output/error_list.txt"

def error_list(err_string):
    try:
        error_file = open(error_filename, "a")
        error_file.write(err_string + "\n")
    except:
        print "ERROR writing to error file! last message: " + str(err_string)
        raw_input("PRESS ENTER TO CONTINUE")


argv = sys.argv
argv = argv[argv.index("--") + 1:]
in_file = argv[0]

print "==========="
print "Importing file: " + in_file
print "==========="
config = dict(**NifConfig.DEFAULTS)
config["IMPORT_FILE"] = in_file
config["IMPORT_SKELETON"] = 0
NifImport(**config)

# try to detect Better Clothes skeleton
altskeleton = False
try:
        arm = bpy.data.armatures["Bip01"]
except KeyError, e:
        error_list(in_file + "(Clothing conversion) Error trying to read armature[Bip01].")
        print "ERROR reading armature[Bip01]. Niffile:[" + in_file + "] may already be converted. Quiting..."
        Blender.Quit()
bone = arm.bones["Bip01 Pelvis"]
if (bone.head["ARMATURESPACE"][0] != 0):
        altskeleton = True
        #raw_input("Bad Skeleton detected")

### **** Changed to be done during modexporter NIF creation
## repose skeleton before unparenting meshes
#bpy.data.objects["Bip01"].setEuler(0, 0, 90)


#unparent meshes
for ob in bpy.data.objects:
	ob.clrParent(2)

##listobj = list()
##for ob in bpy.data.objects:
##        if ob.type == "Mesh":
##                listobj.append(ob)
##for ob in bpy.data.objects:
##        if ob.type == "Armature":
##                root = ob
##for arm in bpy.data.armatures:
##        root = bpy.data.objects[arm.name]
##        for key in arm.bones.keys():
##               bonename = key
##               break
##root.makeParentBone(listobj, bonename)

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
                else:
                        ob.setLocation(ob.loc[0], ob.loc[1]+0.12, ob.loc[2])                        
		#ob.setSize(0.9, 0.9, 0.9)
		#ob.setLocation(ob.loc[0], ob.loc[1], ob.loc[2]-0.03)
		#ob.select(True)
##                if (resetbones == True):
##                        ob.setLocation(ob.loc[0], ob.loc[1], ob.loc[2]-0.75)
##                        ob.setEuler(0,0,0.5*math.pi)
##                else:
##                        ob.setLocation(ob.loc[0], ob.loc[1], ob.loc[2]-0.9)

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

#out_file = in_file[:len(in_file)-4] + "_tes4.nif"
out_file = in_file
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
