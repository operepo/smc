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
if os.name is 'nt' and request.is_scheduler is False:
    # Should be the parent folder of web2py - where the start_smc.bat file is
    curr_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))
    bat_path = os.path.join(curr_path, "kill_smc.bat")
    if os.path.exists(bat_path) is not True:
        f = open(bat_path, 'w')
        f.write("@echo off\r\ntaskkill /f /pid ")
        f.write(str(os.getpid()))
        f.write("\r\n")
        f.close()


def get_app_folders():
    # Will return calculated folders we will need
    # see return statement for values returned

    # Get the full path for this file
    this_file = os.path.abspath(__file__)
    # Get the models folder
    models_folder = os.path.dirname(this_file)
    # app folder
    app_folder = os.path.dirname(models_folder)

    # Applications folder (app parent folder)
    applications_folder = os.path.dirname(app_folder)
    # w2py Root folder
    w2py_folder = os.path.dirname(applications_folder)

    # static folder
    # static_folder = os.path.join(app_folder, "static")
    # media folder
    # media_folder = os.path.join(static_folder, "media")

    #controllers_folder = os.path.join(app_folder, "controllers")
    #cron_folder = os.path.join(app_folder, "cron")
    #databases_folder = os.path.join(app_folder, "databases")
    #errors_folder = os.path.join(app_folder, "errors")
    #languages_folder = os.path.join(app_folder, "languages")
    #private_folder = os.path.join(app_folder, "private")
    #modules_folder = os.path.join(app_folder, "modules")
    #sessions_folder = os.path.join(app_folder, "sessions")
    #uploads_folder = os.path.join(app_folder, "uploads")
    #views_folder = os.path.join(app_folder, "views")

    # win ffmpeg folder
    #win_ffmpeg_folder = os.path.join(w2py_folder, "ffmpeg", "bin")

    return w2py_folder, applications_folder, app_folder


