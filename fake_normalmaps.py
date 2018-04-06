import os
from shutil import copyfile

output_dir = "c:/Oblivion.output/data/textures/"

def recurse_dir(dirname=""):
    if (dirname == ""):
        top_dir = output_dir
    else:
        top_dir = dirname
    if os.path.exists(top_dir):
        for filename in os.listdir(top_dir):
            if os.path.isdir(top_dir+filename):
                filename += "/"
                recurse_dir(top_dir + filename)
                continue
            if ("_n.dds" in filename.lower()):
                continue
            normal_name = filename[:len(filename)-4] + "_n.dds"
            if os.path.exists(top_dir + normal_name):
                continue
            try:
                copyfile("template_n.dds", top_dir+normal_name)
            except:
                raw_input("Error trying to create normalmap for: " + filename)
                continue

recurse_dir()
