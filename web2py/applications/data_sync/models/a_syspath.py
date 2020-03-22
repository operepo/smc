# Make sure web2py reloads modules
from gluon.custom_import import track_changes
track_changes(True)

# Make sure to add our module path to the syspath for this app so that modules are loaded properly
import os
import sys


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

def get_chunk_path():
    # Return the save path for chunks
    (w2py_folder, applications_folder, app_folder) = get_app_folders()

    chunk_path = os.path.join(app_folder, "static/chunks")
    os.makedirs(chunk_path, exist_ok=True)
    return chunk_path


    