import os
from shutil import copyfile
import pdb
import math
from gimpfu import *

# 1. menus/icons - resize to 64x64
# 2. lowres - resize length to divide by 8 or length=64 min
# 3. all images in \data\textures to dds (skipping lowres and icons)
# 4. make normal maps for #3, set alpha channel to 50%, output to _n.dds
# 5. copy and rename 8x8_n.dds for #2

specular_strength = 0.27
mgso_specular_fix = 25

log_messages = False
print_messages = False
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



#1. recurse through textures/menus/...
# - load image
# - verify that it is an icon (32x32)
# - resize to 64x64
# - save as dds (dxt1?)
def resize_icons(file_path):
    filename = os.path.basename(file_path)
    # load file
    #debug_output("DEBUG: loading: " + top_dir+filename + "...")
    try:
        image = pdb.gimp_file_load(file_path, filename)
    except:
        try:
            image = pdb.file_tga_load(file_path, filename)
        except:
            debug_output("ERROR trying to load: " + file_path + ", skipping...")
            return -1
            #pdb.gimp_quit(-1)
    #debug_output("DEBUG: " + top_dir+filename + " loaded.")
    # check dimensions
    if (image.height != 64) or (image.width != 64):
        # resize to 64x64
        debug_output("DEBUG: scaling: " + file_path + "...")
        pdb.gimp_image_scale(image, 64, 64)
    else:
        debug_output("DEBUG: already 64x64: " + file_path)
        # continue with save step to optimize format (dxt1)
    # save
    debug_output("DEBUG: saving: " + file_path + "...")
    pdb.file_dds_save(image, image.active_layer, #image, drawyable/layer
                      file_path, filename, #filename, raw-filename
                      1, # compression: 0=none, 1=bc1/dxt1, 2=bc2/dxt3, 3=bc3/dxt5, 4=BC3n/dxt5nm, ... 8=alpha exponent... 
                      1, # mipmaps: 0=no mipmaps, 1=generate mipmaps, 2=use existing mipmaps(layers)
                      0, # savetype: 0=selected layer, 1=cube map, 2=volume map, 3=texture array
                      0, # format: 0=default, 1=R5G6B5, 2=RGBA4, 3=RGB5A1, 4=RGB10A2
                      -1, # transparent_index: -1 to disable (indexed images only)
                      0, # filter for generated mipmaps: 0=default, 1=nearest, 2=box, 3=triangle, 4=quadratic, 5=bspline, 6=mitchell, 7=lanczos, 8=kaiser
                      0, # wrap-mode for generated mipmaps: 0=default, 1=mirror, 2=repeat, 3=clamp
                      0, # gamma_correct: use gamma corrected mipmap filtering
                      0, # srgb: use sRGB colorspace for gamma correction
                      2.2, # gamma: gamma value used for gamma correction (ex: 2.2)
                      1, # perceptual_metric: use a perceptual error metric during compression
                      0, # preserve_alpha_coverage: preserve alpha test coverage for alpha channel maps
                      0) # alpha_test_threshold: alpha test threshold value for which alpha test coverage should be preserved
    #debug_output("DEBUG: unloading: " + top_dir+filename)
    gimp.delete(image)



def run(file_path):
    #debug_output("Resizing icon...")
    resize_icons(file_path)
    #pdb.gimp_quit(0)



if __name__ == "__main__":
    debug_output("This is a GIMP utility script that is designed to only be called by another script.  Exiting.")

    
