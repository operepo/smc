
# Make sure to add our module path to the syspath for this app so that modules are loaded properly
import os
import sys

spath_imported = False

import_path = os.path.join(request.folder,'modules')
if (import_path not in sys.path):
    sys.path.append(import_path)
    spath_imported = True
