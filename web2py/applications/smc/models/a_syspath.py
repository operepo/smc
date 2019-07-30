# -*- coding: utf-8 -*-

# Make sure web2py reloads modules
from gluon.custom_import import track_changes
track_changes(True)

# Make sure to add our module path to the syspath for this app so that modules are loaded properly
import os
import sys

global APP_VERSION
APP_VERSION = None

sys_path_imported = False

# Needed because w2p import sucks and can't find modules in the modules folder
import_path = os.path.join(request.folder, 'modules')
if import_path not in sys.path:
    sys.path.append(import_path)
    sys_path_imported = True


# If windows, write a kill bat file to end the web2py process
# This is nice so we don't have to track the current PID when it starts and use taskkill
if os.name is 'nt' and request.is_scheduler is False:
    # Should be the parent folder of web2py - where the start_smc.bat file is
    curr_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))
    bat_path = os.path.join(curr_path, "kill_smc.bat")
    if os.path.exists(bat_path) is not True:
        print("Writing " + str(bat_path))
        kill_smc_f = open(bat_path, 'w')
        kill_smc_f.write("@echo off\r\ntaskkill /f /pid ")
        kill_smc_f.write(str(os.getpid()))
        kill_smc_f.write("\r\n")
        kill_smc_f.close()


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

    # controllers_folder = os.path.join(app_folder, "controllers")
    # cron_folder = os.path.join(app_folder, "cron")
    # databases_folder = os.path.join(app_folder, "databases")
    # errors_folder = os.path.join(app_folder, "errors")
    # languages_folder = os.path.join(app_folder, "languages")
    # private_folder = os.path.join(app_folder, "private")
    # modules_folder = os.path.join(app_folder, "modules")
    # sessions_folder = os.path.join(app_folder, "sessions")
    # uploads_folder = os.path.join(app_folder, "uploads")
    # views_folder = os.path.join(app_folder, "views")

    return w2py_folder, applications_folder, app_folder


def get_app_version():
    global APP_VERSION

    if APP_VERSION is None or APP_VERSION == "":
        # Dummy value - use this in case reading the file fails
        APP_VERSION = "v1.9"

        (w2py_folder, applications_folder, app_folder) = get_app_folders()

        app_ver_path = os.path.join(app_folder, 'private', 'app_version.txt')
        if os.path.exists(app_ver_path):
            try:
                app_ver_path_f = open(app_ver_path, 'r')
                APP_VERSION = app_ver_path_f.read().strip()
                app_ver_path_f.close()
            except Exception as ex:
                print("Error reading the app version file, using default: " + str(APP_VERSION) + "<br />" + str(ex))
        else:
            # print("No private/app_version.txt exists... Setting to " + str(APP_VERSION))
            pass

    return APP_VERSION
