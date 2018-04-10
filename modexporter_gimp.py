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
    with open(error_filename, "a") as error_file:
        error_file.write(message + "\n")

def run():
    gimp.message("Script Started...")
    gimp.message("Resizing icons...")
    resize_icons()
    resize_icons(output_dir + "menus50/icons/")
    resize_icons(output_dir + "menus80/icons/")
    gimp.message("Resizing lowres/lod textures...")
    resize_lowres()
    gimp.message("Converting all images to DDS...")    
    convert_textures()
    gimp.message("Script Complete!")



def fake_normalmap_file(filedir, filename):
    # check for _n or _g in name
    if ("_n.dds" in filename.lower()) or ("_g.dds" in filename.lower()):
        return
    # create normal name
    normal_name = filename[:len(filename)-4] + "_n.dds"
    # check if exists, and delete
    if os.path.exists(filedir + normal_name):
        os.remove(filedir + normal_name)
    try:
        copyfile("8x8_n.dds", filedir + normal_name)
    except:
        debug_output("Error trying to create normalmap for: " + filename)
        return



def make_normalmap_file(image, filedir, filename):
    # check for _n or _g in name
    if ("_n.dds" in filename.lower()) or ("_g.dds" in filename.lower()):
        return
    #debug_output("DEBUG: Beginning normalmap generation for: " + filename)
    # set new filename
    new_filename = filename[:len(filename)-4] + "_n.dds"
    # check if normal map exists, return
    if os.path.exists(filedir + new_filename):
        return
    # use normalmaps plugin
    #debug_output("DEBUG: running normalmap() plugin...")
    pdb.plug_in_normalmap(image, image.active_layer, #image, drawable
                          0, # Filter type (0 = 4 sample, 1 = sobel 3x3, 2 = sobel 5x5, 3 = prewitt 3x3, 4 = prewitt 5x5, 5-8 = 3x3,5x5,7x7,9x9)
                          0, # Minimun Z (0 to 1)
                          10, # Scale (> 0)
                          0, # Wrap (0 = no)
                          0, # Height source (0 = average RGB, 1 = alpha channel)
                          0, # Alpha (0 = unchanged, 1 = set to height, 2 = set to inverse height, 3 = set to 0, 4 = set to 1, 5 = invert, 6 = set to alpha map value)
                          0, # Conversion (0 = None, 1 = Biased RGB, 2 = Red, 3 = Green, 4 = Blue, 5 = Max RGB,
                             # 6 = Min RGB, 7 = Colorspace, 8 = Normalize only, 9 = Convert to height map)
                          0, # DU/DV map (0 = none, 1 = 8-bit, 2 = 8-bit unsigned, 3 = 16-bit, 4 = 16-bit unsigned)
                          0, 0, # Invert X component of normal, Invert Y component
                          0, # Swap RGB components
                          0, # Height contrast (0 to 1). If converting to a height map, this value is applied to the results
                          image.active_layer) # Alpha map drawable

##    # decompose
##    debug_output("DEBUG: separating alpha channel...")
##    new_images = pdb.plug_in_decompose(image, image.active_layer, #image, drawable
##                                       "RGBA", # What to decompose: "RGB", "Red", "Green", "Blue", "RGBA", "HSV", "Hue", "Saturation", "Value", "HSL", "Hue (HSL)",
##                                               # "Saturation (HSL)", "Lightness", "CMY", "Cyan", "Magenta", "Yellow", "CMYK", "Cyan_K", "Magenta_K", "Yellow_K", "Alpha",
##                                               # "LAB", "YCbCr_ITU_R470", "YCbCr_ITU_R709", "YCbCr_ITU_R470_256", "YCbCr_ITU_R709_256"
##                                       1) # Create channels as layers in a single image
    # setforeground color
    #debug_output("DEBUG: gimp.set_foreground()")
    gimp.set_foreground(0.3, 0.3, 0.3)
    # mask layer with "transfer to alpha"
    mask = pdb.gimp_layer_create_mask(image.layers[0], 3)
    pdb.gimp_layer_add_mask(image.layers[0], mask)
    # select mask with "replace selection"
    pdb.gimp_image_select_item(image, 2, mask)
    # fill selection with foreground   
    #debug_output("DEBUG: setting alpha channel values...")
    pdb.gimp_edit_fill(mask, 0)
    # apply mask
    pdb.gimp_layer_remove_mask(image.layers[0], 0)
    #new_images[0].layers[3].fill(0) # 0 = foreground color
##    # recompose
##    debug_output("DEBUG: recombining alpha channel into normalmap...")
##    pdb.plug_in_recompose(new_images[0], new_images[0].active_layer) #image, drawable
    # save dds
    debug_output("DEBUG: saving normalmap: " + new_filename)
    pdb.file_dds_save(image, image.active_layer, #image, drawyable/layer
                      filedir + new_filename, new_filename, #filename, raw-filename
                      3, # compression: 0=none, 1=bc1/dxt1, 2=bc2/dxt3, 3=bc3/dxt5, 4=BC3n/dxt5nm, ... 8=alpha exponent... 
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
    #debug_output("Completed: normalmap generation for: " + filename)



#1. recurse through textures/menus/...
# - load image
# - verify that it is an icon (32x32)
# - resize to 64x64
# - save as dds (dxt1?)
def resize_icons(dirname=""):
    debug_output("DEBUG: resize_icons() started...")
    if (dirname == ""):
        top_dir = output_dir + "menus/icons/"
    else:
        top_dir = dirname
    if os.path.exists(top_dir):
        debug_output("DEBUG: searching top_dir: " + top_dir + "...")
        for filename in os.listdir(top_dir):
            if os.path.isdir(top_dir+filename):
                # recurse down and do check below
                filename += "/"
                resize_icons(top_dir + filename)
                continue
            # load file
            #debug_output("DEBUG: loading: " + top_dir+filename + "...")
            try:
                image = pdb.gimp_file_load(top_dir+filename, filename)
            except:
                try:
                    image = pdb.file_tga_load(top_dir+filename, filename)
                except:
                    debug_output("ERROR trying to load: " + top_dir+filename + ", skipping...")
                    continue                           
            #debug_output("DEBUG: " + top_dir+filename + " loaded.")
            # check dimensions
            if (image.height != 64) or (image.width != 64):
                # resize to 64x64
                debug_output("DEBUG: scaling: " + top_dir+filename + "...")
                pdb.gimp_image_scale(image, 64, 64)
            else:
                debug_output("DEBUG: already 64x64: " + top_dir+filename)
                # continue with save step to optimize format (dxt1)
            # save
            debug_output("DEBUG: saving: " + top_dir+filename + "...")
            pdb.file_dds_save(image, image.active_layer, #image, drawyable/layer
                              top_dir+filename, filename, #filename, raw-filename
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
            # end for loop
        # if top_dir exists
    # end resize_icons()


#2. - recurse through textures/lowres/...
# - load image
# - reduce to 64 x ____
# - save as dds (dxt1?)
def resize_lowres(dirname=""):
    debug_output("DEBUG: resize_lowres() started...")
    if (dirname == ""):
        top_dir = output_dir + "lowres/"
    else:
        top_dir = dirname
    if os.path.exists(top_dir):
        debug_output("DEBUG: searching top_dir: " + top_dir + "...")
        # first, build list
        file_list = list()
        for filename in os.listdir(top_dir):
            file_list.append(filename)
        # now iterate through list rather than directly to listdir()
        for filename in file_list:
            if os.path.isdir(top_dir+filename):
                # recurse down and do check below
                filename += "/"
                resize_lowres(top_dir + filename)
                continue
            # load file
            #debug_output("DEBUG: loading: " + top_dir+filename + "...")
            try:
                image = pdb.gimp_file_load(top_dir+filename, filename)
            except:
                try:
                    image = pdb.file_tga_load(top_dir+filename, filename)
                except:
                    debug_output("ERROR trying to load: " + top_dir+filename + ", skipping...")
                    continue
            use_width = False
            width = image.width
            height = image.height
            if (width < height):
                shortlength = width
                use_width = True
            else:
                shortlength = height
            if (shortlength <= 64):
                debug_output("DEBUG: image dimensions too small: [" + str(width) + " x " + str(height) + "], no need to scale.")
                # continue with save step to optimize format (dxt1)
            else:
                shortlength = shortlength / 8
                if (shortlength < 64):
                    shortlength = 64
                # resize shortest dimension to div8 or minimum 64
                if (use_width == True):
                    ratio = float(shortlength) / float(width)
                    longlength = int(height * ratio)
                    debug_output("DEBUG: scaling to: [" + str(shortlength) + " x " + str(longlength) + "]...")
                    pdb.gimp_image_scale(image, shortlength, longlength)
                else:
                    ratio = float(shortlength) / float(height)
                    longlength = int(width * ratio)
                    debug_output("DEBUG: scaling to: [" + str(longlength) + " x " + str(shortlength) + "]...")
                    pdb.gimp_image_scale(image, longlength, shortlength)
            # save
            debug_output("DEBUG: saving: " + top_dir+filename + "...")
            pdb.file_dds_save(image, image.active_layer, #image, drawyable/layer
                              top_dir+filename, filename, #filename, raw-filename
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
            fake_normalmap_file(top_dir, filename)
            gimp.delete(image)
            # end for loop
         # if top_dir exists       
    # end resize_lowres





#3. - recurse through textures/...
# - skip menus and lowres
# - save as dds (dxt5)
def convert_textures(dirname=""):
    debug_output("DEBUG: convert_textures() started...")
    if (dirname == ""):
        top_dir = output_dir
    else:
        top_dir = dirname
    # skip icons or lowres directories
    if ("/icons/" in top_dir.lower()) or ("/lowres/" in top_dir.lower()):
        debug_output("skipping icons/lowres textures...")
        return
    if os.path.exists(top_dir):
        debug_output("DEBUG: searching top_dir: " + top_dir + "...")
        # first, build list
        file_list = list()
        for filename in os.listdir(top_dir):
            file_list.append(filename)
        # now iterate through list rather than directly to listdir()
        for filename in file_list:
            # skip icons or lowres filename
            if ("icons" == filename.lower()) or ("lowres" == filename.lower()) :
                debug_output("skipping icons/lowres textures...")
                continue
            if os.path.isdir(top_dir+filename):
                # recurse down and do check below
                filename += "/"
                convert_textures(top_dir + filename)
                continue
            # load file
            #debug_output("DEBUG: loading: " + top_dir+filename + "...")
            try:
                image = pdb.gimp_file_load(top_dir+filename, filename)
            except:
                try:
                    image = pdb.file_tga_load(top_dir+filename, filename)
                except:
                    debug_output("ERROR trying to load: " + top_dir+filename + ", skipping...")
                    continue   
            # save
            debug_output("DEBUG: saving: " + top_dir+filename + "...")
            pdb.file_dds_save(image, image.active_layer, #image, drawyable/layer
                              top_dir+filename, filename, #filename, raw-filename
                              3, # compression: 0=none, 1=bc1/dxt1, 2=bc2/dxt3, 3=bc3/dxt5, 4=BC3n/dxt5nm, ... 8=alpha exponent... 
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
            try:
                make_normalmap_file(image, top_dir, filename)
            except Exception as e:
                debug_output("ERROR: trying to make normalmap: " + str(e))
            gimp.delete(image)
            # end for loop
         # if top_dir exists       
    # end resize_lowres




if __name__ == "__main__":
        print "Running as __main__ with args: %s" % sys.argv


### pygimp required stuff
##register(
##        "python_modexporter_script",
##        "Batch processing for ModExporter textures",
##        "Running this command will execute the Batch processing script for ModExporter output textures",
##        "modexporter",
##        "no copyright",
##        "2018",
##        "<Toolbox>/Tools/ModExporter Batch Process",
##        "",
##        [],
##        [],
##        modexporter_gimp)
##
##main()
