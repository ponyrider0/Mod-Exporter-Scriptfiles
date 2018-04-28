import bpy
import Blender
from Blender import Scene, Mesh, Object, sys
#from BPyMesh_redux_con import redux
from BPyMesh import redux
import copy
import gc
import threading, thread
import time
import sys
import logging

import os.path

if (os.environ.get("HOME") is not None):
    sys.path.append(os.environ["HOME"])

#from pyffi.formats.nif import NifFormat
#from pyffi.spells.nif.check import SpellCompareSkinData
#from pyffi.spells.nif import NifToaster
from nif_common_con import NifConfig
#from nif_common_con import NifFormat
from import_nif_con import NifImport
from export_nif_con import NifExport

import pyffi.utils.quickhull

if (os.environ.get("MODEXPORTER_OUTPUTROOT") is not None):
    outputRoot = os.environ["MODEXPORTER_OUTPUTROOT"] + "/"
else:
    outputRoot = "C:/"
error_filename = outputRoot + "Oblivion.output/error_list.txt"

class Timeout(threading.Thread):
    def cancel(self):
        self.cancel_timer = True
    def __init__(self,timeout):
        threading.Thread.__init__(self)
        self.timeout = timeout
        self.Failed = False
        self.cancel_timer = False
        self.setDaemon(True)
        #print "*******STARTING TIMER*************"
    def run(self):
        time.sleep(self.timeout)
        if (self.cancel_timer == False):
            self.Failed = True
            #print "!!!!!!!!!TIMED OUT!!!!!!!!!!!!"
            thread.interrupt_main()
        else:
            return

def error_list(err_string):
    try:
        error_file = open(error_filename, "a")
        error_file.write(err_string + "\n")
    except:
        print "ERROR writing to error file! last message: " + str(err_string)
        raw_input("PRESS ENTER TO CONTINUE")


def filter_collision_children(collision_ob):
    # identify all children
    for ob_child in bpy.data.scenes.active.objects:
        if (ob_child.getParent() == collision_ob):
            #print "Processing child of [" + collision_ob.name + "]: " + ob_child.name
            # remove from ob_selection if present
            if ob_child in ob_selection:
                ob_selection.remove(ob_child)
                #print "Removing " + ob_child.name + " from ob_selection..."
            # modify attributes for collision export
            #ob_child.name = "collision_bad"
            ob_child.setDrawType(1)
            ob_child.setDrawMode(32)
            ob_child.rbShapeBoundType = 4
            #ob_child.select(True)
            if (ob_child not in collision_selection):
                collision_selection.append(ob_child)
            # recurse for all children
            filter_collision_children(ob_child)
                

def hull_convex(ob, me, selected_only, precision = 0.1):
    """Hull mesh in a convex shape."""
    # find convex hull
    vertices, triangles = pyffi.utils.quickhull.qhull3d(
        [tuple(v.co) for v in me.verts if v.sel or not selected_only],
        precision = precision)
    # create convex mesh
    box = Blender.Mesh.New('convexpoly')
    for vert in vertices:
        box.verts.extend(*vert)
    for triangle in triangles:
        box.faces.extend(triangle)
    # link mesh to scene and set transform
    scn = Blender.Scene.GetCurrent()
    boxob = scn.objects.new(box, 'convexpoly')
    boxob.setMatrix(ob.getMatrix('worldspace'))
    # set bounds type
    boxob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
    boxob.rbShapeBoundType = 5 # convex hull shape not in blender Python API; Blender.Object.RBShapes['CONVEXHULL']?
    boxob.drawMode = Blender.Object.DrawModes['WIRE']

def poly_reduce(ob, reduction = 0.5):
    act_ob = ob
    if not act_ob or act_ob.type != 'Mesh':
        return
    act_me = act_ob.getData(mesh=1)
    if act_me.multires:
        return
    act_group= act_me.activeGroup
    if not act_group: act_group= ''
    # Defaults
    PREF_REDUX= reduction
    PREF_BOUNDRY_WEIGHT= 5.0
    PREF_REM_DOUBLES= False
    PREF_FACE_AREA_WEIGHT= 1.0
    PREF_FACE_TRIANGULATE= False
    VGROUP_INF_ENABLE= 0
    VGROUP_INF_REDUX= act_group
    VGROUP_INF_WEIGHT= 10.0
    PREF_DO_UV= 1
    PREF_DO_VCOL= 1
    PREF_DO_WEIGHTS= 1
    PREF_OTHER_SEL_OBS= 0
    t= Blender.sys.time()
    print 'reducing:', act_ob.name, act_ob.getData(1)
    redux(act_ob, PREF_REDUX, PREF_BOUNDRY_WEIGHT, PREF_REM_DOUBLES, PREF_FACE_AREA_WEIGHT, PREF_FACE_TRIANGULATE, PREF_DO_UV, PREF_DO_VCOL, PREF_DO_WEIGHTS, VGROUP_INF_REDUX, VGROUP_INF_WEIGHT)
    if PREF_OTHER_SEL_OBS:
        for ob in scn.objects.context:
            if ob.type == 'Mesh' and ob != act_ob:
                print 'reducing:', ob.name, ob.getData(1)
                redux(ob, PREF_REDUX, PREF_BOUNDRY_WEIGHT, PREF_REM_DOUBLES, PREF_FACE_AREA_WEIGHT, PREF_FACE_TRIANGULATE, PREF_DO_UV, PREF_DO_VCOL, PREF_DO_WEIGHTS, VGROUP_INF_REDUX, VGROUP_INF_WEIGHT)
                #Window.RedrawAll()
    print 'Reduction done in %.6f sec.' % (Blender.sys.time()-t)

#=================== start script =========================
#logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)
Blender.Set("texturesdir", outputRoot + "Oblivion.output/Data/Textures/")
argv = sys.argv
#print "full argumentlist: " + str(argv)
argv = argv[argv.index("--") + 1:]
#print "Processed arguments: " + str(argv)
out_file = argv[0]
# Assuming "/data/meshes" in path, redirect to /Temp/Meshes
in_file = out_file.lower().replace("/data/meshes/", "/temp/meshes/")
if os.path.exists(in_file) == False:
    print "Input file not found! skipping file..."
    Blender.Quit()
if os.path.exists(out_file) == True:
    print "Output file already exists, skipping file..."
    Blender.Quit()
fullres_collisions = True
if ("--fullres_collisions" in argv):
    fullres_collisions = bool(int(argv[argv.index("--fullres_collisions") + 1]))
if ("--reduction_scale" in argv):
    reduction_scale = int(argv[argv.index("--reduction_scale") + 1])
else:
    reduction_scale = 0.75

#start import
config = dict(**NifConfig.DEFAULTS)
config["IMPORT_FILE"] = in_file
print "----------"
print "Importing: " + in_file
try:
    nifimport = NifImport(**config)
except KeyboardInterrupt:
    error_list(in_file + " (NifImport - keyboard interrupt)")
    raw_input("Keyboard interrupt detected, will skip current operation: import[" + in_file + "]. Press Enter to continue with next file.")
    #return
    Blender.Quit()
except RuntimeError, e:
    # delete all objects and move on to next input
    print "RuntimeError: unable to import: [" + in_file + "], message: [" + str(e) + "], skipping..."
    error_list(in_file + " (NifImport - Runtime error): " + str(e) )
    raw_input("Press Enter to continue.")
    #return
    Blender.Quit()
except KeyError, e:
    unknown_error = ""
    if isinstance(e, basestring):
        unknown_error = e
    else:
        unknown_error = str(e)
    print "Exception: KeyError occured during Import: [" + in_file + "], error=[" + unknown_error + "], skipping..."
    error_list(in_file + " (NifImport - KeyError Exception): " + unknown_error)
    #return
    Blender.Quit()
except TypeError, e:
    unknown_error = ""
    if isinstance(e, basestring):
        unknown_error = e
    else:
        unknown_error = str(e)
    print "Exception: TypeError occured during Import: [" + in_file + "], error=[" + unknown_error + "], skipping..."
    error_list(in_file + " (NifImport - TypeError Exception): " + unknown_error)
    #return
    Blender.Quit()
except ValueError, e:
    unknown_error = ""
    if isinstance(e, basestring):
        unknown_error = e
    else:
        unknown_error = str(e)
    print "Exception: ValueError occured during Import: [" + in_file + "], error=[" + unknown_error + "], skipping..."
    error_list(in_file + " (NifImport - ValueError Exception): " + unknown_error)
    #return
    Blender.Quit()
except AttributeError, e:
    unknown_error = ""
    if isinstance(e, basestring):
        unknown_error = e
    else:
        unknown_error = str(e)
    print "Exception: AttributeError occured during Import: [" + in_file + "], error=[" + unknown_error + "], skipping..."
    error_list(in_file + " (NifImport - AttributeError Exception): " + unknown_error)
    #return
    Blender.Quit()
except Exception, e:
    unknown_error = str(e)
    print "ERROR: un-handled exception returned! [" + in_file + "], error=[" + unknown_error + "], skipping..."
    error_list(in_file + " (NifImport - AttributeError Exception): " + unknown_error)
    Blender.Quit()
#Post import debugging
config["ALPHA_PROP_FLAGS"] = nifimport.ALPHA_PROP_FLAGS
config["ALPHA_PROP_THRESHOLD"] = nifimport.ALPHA_PROP_THRESHOLD
#if (config["ALPHA_PROP_THRESHOLD"] != 0) or (config["ALPHA_PROP_FLAGS"] != 0x12ED):
#    raw_input("ALPHA_PROP_FLAGS=" + str(config["ALPHA_PROP_FLAGS"]) + ", ALPHA_PROP_THRESHOLD=" + str(config["ALPHA_PROP_THRESHOLD"]) + ". Press ENTER to continue...")


#process objects, select meshes, ID/generate collision meshes
print "----------"
print "Selecting objects for export..."
bpy.data.scenes.active.objects.selected = []
ob_selection = list()
collision_selection = list()
for ob in bpy.data.scenes.active.objects:
    if (ob.getType() == "Mesh"):
        for mat in ob.data.materials:
            if (mat.getHardness() < 5):
                mat.setHardness(mat.getHardness()*100)
            #noname material crashfix
            if ("noname" in mat.name.lower()):
                mat.name = mat.name.lower().replace("noname", "material")
    if (True):
        # look for drawtype = shaded or textured
        if ("collision" in ob.name.lower()) or (ob.getDrawType() == 1):
            #track collision objects to separate all their children from ob_selection list
            print "Collision mesh found: " + ob.name
            collision_selection.append(ob)
            #ob.select(True)
        elif (ob.getDrawType() == 4) and ("collision" not in ob.name.lower()):
            print "Selecting mesh for export: " + ob.name
            ob_selection.append(ob)
            #ob.select(True)
        else:
            print "skipping: " + ob.name
    else:
        print "skipping: " + ob.name
# selection step 2: filter collision_selection out of ob_selection
if (collision_selection != []):
    print "----------"
    print "Sorting collision and object meshes..."
    for collision_ob in collision_selection:
        print "Processing: " + collision_ob.name
        if collision_ob in ob_selection:
            ob_selection.remove(collision_ob)
            #print "Removing " + collision_ob.name + " from ob_selection..."
        #collision_ob.name = "collision"
        collision_ob.setDrawType(1)
        collision_ob.setDrawMode(32)
        collision_ob.rbShapeBoundType = 4
        filter_collision_children(collision_ob)
print "Selection phase complete."
#raw_input("Press ENTER to continue.")



#_far.nif processing: polyreduce and fix noname material Oblivion bugs
if ("_far.nif" in in_file):
    print "----------"
    print "VWD/LOD (*_far.nif) detected, performing optimizations for Oblivion"
    for ob in ob_selection:
        if (ob.getType() != "Mesh"):
            continue
        #polyreduce (run on all selected objs)
        try:
            global_timeout = False
            timeout = Timeout(10)
            timeout.start()
            poly_reduce(ob, reduction_scale)
            timeout.cancel()
        except KeyboardInterrupt:
            if (timeout.Failed == True):
                print("poly_reduce Operation timed out. Skipping to next step.")
                error_list(in_file + " (poly_reduce - operation timed out)")                                                
                #raw_input("Operation timed out: poly_reduce[" + in_file + "]. Press Enter to skip poly_reduce or CTRL-C to stop script.")
            else:
                error_list(in_file + " (poly_reduce - keyboard interrupt)")
                raw_input("Keyboard interrupt detected, will skip current operation: polyreduce[" + in_file + "]. Press Enter to skip poly_reduce.")                                        
            for ob in bpy.data.objects:
                bpy.data.scenes.active.objects.unlink(ob)
            gc.collect()
            continue
        except RuntimeError, e:
            # delete all objects and move on to next input
            print "poly_reduce: RuntimeError exception: [" + in_file + "], message: [" + str(e) + "], skipping..."
            for ob in bpy.data.objects:
                bpy.data.scenes.active.objects.unlink(ob)
            gc.collect()
            error_list(in_file + " (poly_reduce - RuntimeError): " + str(e) )
            #raw_input("Press Enter to continue.")
            continue
        except Exception, e:
            unknown_error = ""
            if isinstance(e, basestring):
                unknown_error = e
            else:
                unknown_error = str(e)
            print "poly_reduce: unhandled exception! [" + in_file + "], error=[" + unknown_error + "], skipping..."
            for ob in bpy.data.objects:
                bpy.data.scenes.active.objects.unlink(ob)
            error_list(in_file + " (poly_reduce - unhandled exception): " + unknown_error)
            #raw_input("Press Enter to continue.")
            continue


#collision geometry generation
if (collision_selection == []) and ("_far.nif" not in in_file):
    print "----------"
    print "No collision mesh found, generating collision mesh..."
    qhull_failed = False
    if (fullres_collisions == False):
        for ob in ob_selection:
            print "qhull(" + ob.name + ")..."
            me = ob.getData(mesh=1) # get Mesh, not NMesh
            # are any vertices selected?
            selected_only = False
            # create mesh by requested type
            try:
                timeout = Timeout(10)
                timeout.start()
                hull_convex(ob, me, selected_only, precision = 0.1)
                timeout.cancel()
            except KeyboardInterrupt:
                if (timeout.Failed == True):
                    print("qhull: Operation timed out, fallingback to full resolution collision mesh...")
                    error_list(in_file + " (qhull - operation timed out)")                                                
                    #raw_input("Operation timed out: qhull[" + in_file + "]. Press Enter to skip qhull or CTRL-C to stop script.")
                else:
                    error_list(in_file + " (qhull - keyboard interrupt)")
                    raw_input("Keyboard interrupt detected, will skip current operation: qhull[" + in_file + "]. Press Enter to skip qhull.")
                qhull_failed = True
                break
            except RuntimeError, e:
                print "qhull: RuntimeError exception: " + in_file + "], message: [" + str(e) + "], skipping..."
                error_list.append(in_file + " (qhull - RuntimeError): " + str(e) )
                #raw_input("Press Enter to continue.")
                qhull_failed = True
                break
            except Exception, e:
                unknown_error = ""
                if isinstance(e, basestring):
                    unknown_error = e
                else:
                    unknown_error = str(e)
                print "qhull: unhandled exception! [" + in_file + "], error=[" + unknown_error + "], skipping..."
                error_list(in_file + " (qhull - unhandled exception): " + unknown_error)
                qhull_failed = True
                #raw_input("Press Enter to continue.")
                break
            print "done."
    if (fullres_collisions == True) or (qhull_failed == True):
        # loop through ob_selection and add duplicate meshes into collision object
        #reset collision_selection
        collision_selection = []
        for ob in ob_selection:
            collision_mesh = copy.copy(ob.getData(mesh=1))
            if (collision_mesh == None):
                continue
            try:
                collision_ob = bpy.data.scenes.active.objects.new(collision_mesh)
            except Exception, e:
                print in_file + " (Error during collision mesh generation): " + str(e) + ", attempting to continue..."
                error_list(in_file + " (Error during collision mesh generation): " + str(e) + ", attempting to continue...")
                continue
            collision_ob.setMatrix(ob.getMatrix())
            collision_ob.setName("collision")
            collision_ob.setDrawType(1)
            collision_ob.setDrawMode(32)
            collision_ob.rbShapeBoundType = 4
            #collision_ob.select(True)
            collision_selection.append(collision_ob)
    print "collision generation complete."


folderPath = os.path.dirname(out_file)
try:
    if os.path.exists(folderPath) == False:
        os.makedirs(folderPath)
except:
    print "Export ERROR: could not create destination directory: " + folderPath
    error_list(in_file + "Export ERROR: could not create destination directory: " + folderPath)
    Blender.Quit()

#start export
config["EXPORT_VERSION"] = 'Oblivion'
config["EXPORT_FILE"] = out_file
print "----------"
if ("_far.nif" not in in_file):
    print "Exporting with collisions: " + out_file
    config["EXPORT_OBJECTS"] = ob_selection + collision_selection
else:
    print "DEBUG: cleaning ob_selection..."
    #raw_input("Press ENTER to continue:")
    for ob in ob_selection:
        if (ob.getDrawType() == 1) or (ob.getDrawMode() == 32):
            print "DEBUG: collision found hiding in ob_selection! [" + ob.name + "]"
            #raw_input("Press ENTER to continue.")
            ob_selection.remove(ob)
            bpy.data.scenes.active.objects.unlink(ob)
            del ob
    for collision_ob in collision_selection:
        print "Unlinking collision object: " + collision_ob.name
        collision_selection.remove(collision_ob)
        bpy.data.scenes.active.objects.unlink(collision_ob)
        del collision_ob
    gc.collect()
    print "Exporting without collisions: " + out_file
    config["EXPORT_OBJECTS"] = ob_selection

#print "DEBUG: ob_selection contains: " + str(ob_selection)
#raw_input("Press ENTER to continue.")
try:
    NifExport(**config)
except KeyboardInterrupt:
    error_list(in_file + " (NifExport - keyboard interrupt)")
    raw_input("Keyboard interrupt detected, will skip current operation: export[" + in_file + "]. Press Enter to continue with next file.")
except AttributeError, e:
    error_list(in_file + " (NifExport - AttributeError): " + str(e))
    print "NifExport: AttributeError exception: " + in_file + "], error: [" + str(e) + "], skipping..."
    #raw_input("Press enter to continue")
except RuntimeError, e:
    error_list(in_file + " (NifExport - RuntimeError): " + str(e))
    print "NifExport: RuntimeError exception: " + in_file + "], message: [" + str(e) + "], skipping..."
    #raw_input("Press enter to continue")
except Exception, e:
    unknown_error = ""
    if isinstance(e, basestring):
        unknown_error = e
    else:
        unknown_error = str(e)
    error_list(in_file + " (NifExport - unhandled exception): " + unknown_error)
    print "NifExport: unhandled exception! [" + in_file + "], error=[" + unknown_error + "], skipping..."
    #raw_input("Press enter to continue")

#done. exit Blender
Blender.Quit()
