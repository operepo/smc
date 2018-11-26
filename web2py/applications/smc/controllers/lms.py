import sys
import os
import subprocess
import urllib
from gluon import current

import paramiko

from ednet.ad import AD
from ednet.canvas import Canvas
from ednet.appsettings import AppSettings
from ednet.util import Util

# Needed for remote connection?
auth.settings.allow_basic_login = True
# auth.settings.actions_disabled.append('login')
# auth.settings.allow_basic_login_only = True
# auth.settings.actions.login_url=URL('your_own_error_page')


@auth.requires_membership("Administrators")
def test():
    #pw = "Sid777777!"
    #enc_pw = "_6tCszfjuGddHJocWIdjR3CXVLU2l0BvgPqbkUaIqVs="
    #enc_pw = Util.encrypt("_6tCszfjuGddHJocWIdjR3CXVLU2l0BvgPqbkUaIqVs=")
    #txt_pw = Util.decrypt(enc_pw,"3e7911db9b4c39309d3d41d393ef861efd8e56f21d257ec8a5d507cc")
    # key = Util.aes_key
    return locals()


@auth.requires_membership("Administrators")
def check_for_student():
    response.view = 'generic.json'
    db = current.db
    full_name = ""
    msg = ""
    user_name = None

    # Get the user in question
    if len(request.args) > 0:
        user_name = request.args[0]
    else:
        msg = "No username specified!"

    # See if user exists in SMC
    if user_name is not None:
        # First - does the user exist?
        user_exists = False
        rows = db(db.auth_user.username == user_name).select(db.auth_user.id,
                                                             db.auth_user.first_name,
                                                             db.auth_user.last_name)
        for row in rows:
            user_exists = True
        if user_exists is True:
            full_name = str(row["last_name"]) + ", " + str(row["first_name"])
            msg = "Found"
        else:
            # User doesn't exit!
            msg = "Invalid User!"

    return dict(msg=msg, full_name=full_name)


@auth.requires_membership("Administrators")
def credential_student():
    response.view = 'generic.json'
    db = current.db
    
    key = ""
    msg = ""
    hash = ""
    user_name = None
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


def get_firewall_list():
    response.view = 'default/index.json'
    db = current.db
    rs = db(db.ope_laptop_firewall_rules).select(db.ope_laptop_firewall_rules.ALL).as_list()
    return response.json(rs)
