import sys
import os
import subprocess

from gluon import current

import paramiko

from ednet.ad import AD
from ednet.canvas import Canvas
from ednet.appsettings import AppSettings


# Needed for remote connection?
auth.settings.allow_basic_login = True
#auth.settings.actions_disabled.append('login')
#auth.settings.allow_basic_login_only = True
#auth.settings.actions.login_url=URL('your_own_error_page')

@auth.requires_membership("Administrators")
def credential_student():
    response.view = 'generic.json'
    db = current.db
    
    key = ""
    msg = ""
    hash = ""
    user_name = ""
    full_name = ""
    # Get the user in question
    if len(request.args) > 0:
        user_name = request.args[0]
    if user_name is not None:
        # First - does the user exist?
        user_exists = False
        rows = db(db.auth_user.username == user_name).select(db.auth_user.id)
        for row in rows:
            user_exists = True
        if user_exists is True:
            key, msg, hash, full_name = Canvas.EnsureStudentAccessToken(user_name)
            
        else:
            # User doesn't exit!
            msg = "Invalid User!"
    return dict(key=key, msg=msg, hash=hash, full_name=full_name)
