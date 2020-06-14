# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import urllib
import json
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
    # pw = "Sid777777!"
    # enc_pw = "_6tCszfjuGddHJocWIdjR3CXVLU2l0BvgPqbkUaIqVs="
    # enc_pw = Util.encrypt("_6tCszfjuGddHJocWIdjR3CXVLU2l0BvgPqbkUaIqVs=")
    # txt_pw = Util.decrypt(enc_pw,"3e7911db9b4c39309d3d41d393ef861efd8e56f21d257ec8a5d507cc")
    # key = Util.aes_key
    return locals()


#@auth.requires_membership("Administrators")
@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def verify_ope_account_in_smc():
    response.view = 'generic.json'
    db = current.db
    student_full_name = ""
    msg = ""
    user_name = None
    laptop_admin_user = ""
    laptop_admin_password = ""

    # Get the student user in question
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
            student_full_name = str(row["last_name"]) + ", " + str(row["first_name"])
            msg = "Found"
        else:
            # User doesn't exit!
            msg = "Invalid User! - User name is CASE SENSITIVE - verify that you typed it exactly as it is in the system."

    if msg == "Found":
        # Pull the laptop admin info
        laptop_admin_user = AppSettings.GetValue("laptop_admin_user", "")
        # Moved pw to credential area
        laptop_admin_password = "********" # AppSettings.GetValue("laptop_admin_password", "")
    
    smc_version = get_app_version()
    return dict(msg=msg, student_full_name=student_full_name,
                laptop_admin_user=laptop_admin_user,
                laptop_admin_password=laptop_admin_password,
                smc_version=smc_version)


#@auth.requires_membership("Administrators")
@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def credential_student():
    response.view = 'generic.json'
    db = current.db
    
    key = ""
    msg = ""
    hash = ""
    user_name = None
    full_name = ""
    laptop_admin_password = ""
    admin_hash = ""
    canvas_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.ed')
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
            # Turn bytes into string so it sends over json better
            if isinstance(hash ,bytes):
                try:
                    hash = hash.decode('utf-8')
                except Exception as ex:
                    hash = "ERROR DECODING HASH!!!"
            # Encode admin hash
            laptop_admin_password = AppSettings.GetValue("laptop_admin_password", "")
            admin_hash = Util.encrypt(laptop_admin_password, key)
            laptop_admin_password = "" # Clear when done
            # Turn bytes into string so it sends over json better
            if isinstance(admin_hash, bytes):
                try:
                    admin_hash = admin_hash.decode("utf-8")
                except Exception as ex:
                    admin_hash = "ERROR DECODING HASH!!!"
            
            # All is good, if there is an ex_info param, then pull data out
            # of it and put it in the ope_laptops data table
            #print(request.vars)
            try:
                info = request.vars["ex_info"]
                if info is not None:
                    print("Saving posted credential information.")
                    record = db((db.ope_laptops.bios_serial_number==info["bios_serial_number"]) &
                        (db.ope_laptops.current_student==info["current_student"])
                    ).select().first()
                    if record is None:
                        # No record, add one
                        db.ope_laptops.insert(
                            bios_serial_number=info["bios_serial_number"],
                            boot_disk_serial_number=info["disk_boot_drive_serial_number"],
                            current_student=info["current_student"],
                            admin_user=info["admin_user"],
                            credentialed_by_user=info["logged_in_user"],
                            last_sync_date=request.now,
                            bios_name=info["bios_name"],
                            bios_version=info["bios_version"],
                            bios_manufacturer=info["bios_manufacturer"],
                            admin_password_status=info["cs_admin_password_status"],
                            extra_info=json.dumps(info),
                        )
                    else:
                        # Update existing record
                        record.update_record(
                            #bios_serial_number=info["bios_serial_number"],
                            boot_disk_serial_number=info["disk_boot_drive_serial_number"],
                            #current_student=info["current_student"],
                            admin_user=info["admin_user"],
                            credentialed_by_user=info["logged_in_user"],
                            last_sync_date=request.now,
                            bios_name=info["bios_name"],
                            bios_version=info["bios_version"],
                            bios_manufacturer=info["bios_manufacturer"],
                            admin_password_status=info["cs_admin_password_status"],
                            extra_info=json.dumps(info),
                        )
                    db.commit()
            except Exception as ex:
                print("ERROR - Invalid json post!\n" + str(ex))

        else:
            # User doesn't exit!
            msg = "Invalid User!"
    return dict(key=key, msg=msg, hash=hash, full_name=full_name, canvas_url=canvas_url,
        admin_hash=admin_hash)


def get_firewall_list():
    response.view = 'default/index.json'
    db = current.db
    rs = db(db.ope_laptop_firewall_rules).select(db.ope_laptop_firewall_rules.ALL).as_list()
    return response.json(rs)
