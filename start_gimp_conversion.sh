#!/bin/bash
export GIMPEXE=/opt/local/bin/gimp
export MODEXPORTER_OUTPUTROOT=$HOME

$GIMPEXE -idf --batch-interpreter python-fu-eval -b "import sys;sys.path=['.']+sys.path;import modexporter_gimp;modexporter_gimp.run()" -b "pdb.gimp_quit(1)"

