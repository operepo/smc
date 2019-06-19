# Make sure web2py reloads modules
from gluon.custom_import import track_changes
track_changes(True)

# Make sure to add our module path to the syspath for this app so that modules are loaded properly
import os
import sys

spath_imported = False

# Needed because w2p import sucks and can't find modules in the modules folder
import_path = os.path.join(request.folder, 'modules')
if import_path not in sys.path:
    sys.path.append(import_path)
    spath_imported = True
