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


# If windows, write a kill bat file to end the web2py process
# This is nice so we don't have to track the current PID when it starts and use taskkill
if os.name is 'nt':
    # Should be the parent folder of web2py - where the start_smc.bat file is
    curr_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))
    bat_path = os.path.join(curr_path, "kill_smc.bat")
    f = open(bat_path, 'w')
    f.write("@echo off\r\ntaskkill /f /pid ")
    f.write(str(os.getpid()))
    f.write("\r\n")
    f.close()



