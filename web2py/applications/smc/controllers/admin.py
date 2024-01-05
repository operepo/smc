# -*- coding: utf-8 -*-

import sys
import os
import subprocess

from gluon import current

import paramiko

from ednet.ad import AD
from ednet.canvas import Canvas
from ednet.appsettings import AppSettings

# Help shut up pylance warnings
if 1==2: from ..common import *


@auth.requires_membership("Administrators")
def laptop_admin_credentials():
    ensure_settings()

    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["laptop_admin_user", "laptop_admin_password"]).process()

    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def laptop_firewall():
    return dict(message="Welcome")


@auth.requires_membership("Administrators")
def laptop_settings():
    ensure_settings()

    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["laptop_admin_user", "laptop_admin_password", "laptop_network_type"]).process()

    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    
    return dict(form=form)


@auth.requires_membership("Administrators")
def index():
    ensure_settings()

    response.view = 'generic.html'
    return dict(message="hello from admin.py")


@auth.requires_membership("Administrators")
def ensure_settings():
    # Check the settings table, there should be one row
    if db(db.my_app_settings).count() < 1:
        # Add a row
        db.my_app_settings.insert()

    # Make sure LDAP is reset after reloading settings
    AD.Close()
    return True


@auth.requires_membership("Administrators")
def config():
    ensure_settings()
    
    return dict()  # test_form=None)


@auth.requires_membership("Administrators")
def config_app_settings():
    ensure_settings()
    
    db.my_app_settings.disable_faculty_self_change_password.label = \
        "Prevent faculty from changing passwords with SMC"
    db.my_app_settings.disable_student_self_change_password.label = \
        "Prevent students from changing passwords with SMC"
    db.my_app_settings.disable_media_auto_play.label = \
        "Disable Auto Play on Media (can override with autoplay=true in the link)"

    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["app_name", "app_description", "app_logo",
                   "disable_student_self_change_password",
                   "disable_faculty_self_change_password",
                   "disable_media_auto_play"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def config_ad_settings():
    ensure_settings()
    
    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["ad_import_enabled", "ad_service_user", "ad_service_password",
                           "ad_server_protocol",
                           "ad_server_address"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        AD.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def config_file_settings():
    ensure_settings()
    
    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["file_server_import_enabled", "file_server_login_user",
                           "file_server_login_pass",
                           "file_server_address", "file_server_quota_drive"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        AD.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def config_zfs_settings():
    ensure_settings()
    msg = ""
    
    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["zpool_enabled", "zpool_server_address", "zpool_login_user",
                           "zpool_login_password",
                           "zpool_source_dataset", "zpool_dest_dataset", "zpool_sync_setting"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        AD.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form, message=msg)    


@auth.requires_membership("Administrators")
def refresh_datasets():
    ensure_settings()

    message = ""
    succeeded = False
    
    zfs_enabled = AppSettings.GetValue('zpool_enabled', False)
    zfs_ip = AppSettings.GetValue('zpool_server_address', '')
    zfs_user = AppSettings.GetValue('zpool_login_user', 'root')
    zfs_pass = AppSettings.GetValue('zpool_login_password', '')
    
    if not zfs_enabled:
        message = "ZFS Server Not Enabled - Check settings..."
        return dict(succeeded=succeeded, message=message)
    
    message = "Connecting (" + zfs_user + "@" + zfs_ip + ")..."
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(zfs_ip, username=zfs_user, password=zfs_pass)
        stdin, stdout, stderr = ssh.exec_command("zfs list -H -o name")
        lines = stdout.readlines()
        ssh.close()
        
        for line in lines:
            line = line.strip()
            if line == "":
                continue
            message += "\nFound Dataset: " + line
            if '.system' in line or 'freenas-boot' in line:
                message += " -- found system or boot dataset, skipping..."
            else:
                # Try to add this to the database
                if db(db.zpool_datasets.name==line).count() < 1:
                    # Add it
                    db.zpool_datasets.insert(name=line)
                else:
                    # Skip it...
                    message += " -- Already added..."
        
        db.commit()
        succeeded = True
    except Exception as e:
        message += "Error getting datasets: " + str(e)
    
    return dict(succeeded=succeeded, message=message)


@auth.requires_membership("Administrators")
def config_faculty_settings():
    ensure_settings()
    
    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["faculty_id_pattern", "faculty_password_pattern", "faculty_email_pattern",
                           "ad_faculty_cn", "ad_faculty_group_cn", "ad_faculty_home_directory",
                           "ad_faculty_home_drive", "ad_faculty_profile_directory",
                           "ad_faculty_login_script_path", "ad_faculty_home_directory_quota"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        AD.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def config_student_settings():
    ensure_settings()
    
    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False,
                   fields=["student_id_pattern", "student_password_pattern", "student_email_pattern",
                           "ad_student_cn", "ad_student_group_cn", "ad_student_home_directory",
                           "ad_student_home_drive", "ad_student_profile_directory",
                           "ad_student_login_script_path", "ad_student_home_directory_quota"]).process()
    
    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        AD.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form)


@auth.requires_membership("Administrators")
def config_canvas_settings():
    ensure_settings()
    msg = ""

    auto_config_form = SQLFORM.factory(submit_button="OPE Auto Configure",
                                       _name="auto_config").process(formname="auto_config")

    if auto_config_form.accepted:
        # Try to auto config
        access_token, msg1 = Canvas.EnsureAdminAccessToken()
        if access_token != "":
            # Pull the canvas URL from the environment
            canvas_url = ""
            try:
                canvas_url = str(os.environ["CANVAS_SERVER"]).strip() + ""
            except KeyError as ex:
                # not set!!
                canvas_url = ""
            if canvas_url != "":
                AppSettings.SetValue('canvas_server_url', canvas_url)
            # Make sure to turn enable the canvas integration if it worked
            AppSettings.SetValue("canvas_import_enabled", True)
            response.flash = "Canvas integration auto configured and enabled"
        else:
            response.flash = "Unable to auto configure canvas integration!" + msg1

    rows = db().select(db.my_app_settings.ALL)
    form = SQLFORM(db.my_app_settings, rows[0], showid=False, _name="canvas_config",
                   fields=["canvas_import_enabled", "canvas_integration_enabled", "canvas_auto_create_courses",
                           "canvas_access_token", "canvas_secret",
                           "canvas_database_server_url",
                           "canvas_database_password", "canvas_server_url",
                           "canvas_student_quota", "canvas_faculty_quota",
                           ]).process(formname="canvas_config")

    if form.accepted:
        # Saved
        response.flash = "Settings Saved!"
        Canvas.Close()
        pass
    elif form.errors:
        response.flash = "Error! " + str(form.errors)
    return dict(form=form, auto_config_form=auto_config_form, msg=msg)


@auth.requires_membership("Administrators")
def switchmode():
    ensure_settings()
    
    online = SQLFORM.factory(submit_button="Set Online Mode", _name="online").process(formname="online")
    
    offline = SQLFORM.factory(submit_button="Set Offline Mode", _name="offline").process(formname="offline")
    
    if online.accepted:
        p = subprocess.Popen("/bin/set_bind_online", shell=True)
        ret = p.wait()
        response.flash = "Online Mode Set!" # + str(ret)
    if offline.accepted:
        p = subprocess.Popen("/bin/set_bind_offline", shell=True)
        ret = p.wait()
        response.flash = "Offline Mode Set!" # + str(ret)
    
    return dict(switch_online=online, switch_offline=offline)


@auth.requires_membership("Administrators")
def switchquota():
    ensure_settings()
    
    disabled = SQLFORM.factory(submit_button="Set Quota Disabled", _name="disabled").process(formname="disabled")
    
    tracking = SQLFORM.factory(submit_button="Set Quota Tracking", _name="tracking").process(formname="tracking")
    
    enforcing = SQLFORM.factory(submit_button="Set Quota Enforcing", _name="enforcing").process(formname="enforcing")
    
    if disabled.accepted:
        if AD.SetQuotaEnabled(False, False) is not True:
            response.flash = "Error setting quota mode to disabled: " + AD.GetErrorString()
        else:
            response.flash = "Quota set to disabled" # + str(ret)
    if tracking.accepted:
        if AD.SetQuotaEnabled(True, False) is not True:
            response.flash = "Error setting quota mode to tracking: " + AD.GetErrorString()
        else:
            response.flash = "Quota set to tracking" # + str(ret)
    if enforcing.accepted:
        if AD.SetQuotaEnabled(True, True) is not True:
            response.flash = "Error setting quota mode to enforcing: " + AD.GetErrorString()
        else:
            response.flash = "Quota set to enforcing" # + str(ret)
    
    return dict(switch_disabled=disabled, switch_tracking=tracking, switch_enforcing=enforcing)


@auth.requires_membership("Administrators")
def verify_settings():
    ensure_settings()

    session.forget(response)  # Don't need the session so don't block on it
    auto_create = False
    ret = ""
    auto = request.vars.get('auto', '')
    if auto == "true":
        auto_create = True
    
    ret += "<h4>Active Directory Settings</h4><div style='font-size: 10px;'>"
    r = AD.VerifyADSettings(auto_create)
    ret += AD.GetErrorString()
    if r is not True:
        ret += "<div style='font-weight: bold; color: red;'>Active Directory Error</div>"
    else:
        ret += "<div style='font-weight: bold; color: green;'>Tests Passed</div>"
    ret += "</div><hr />"
    
    ret += "<h4>Canvas Settings</h4><div style='font-size: 10px;'>"
    r = Canvas.VerifyCanvasSettings()
    ret += Canvas.GetErrorString()
    if r is not True:
        ret += "<div style='font-weight: bold; color: red;'>Canvas Error</div>"
    else:
        ret += "<div style='font-weight: bold; color: green;'>Tests Passed</div>"
    ret += "</div><hr />"

    return ret


@auth.requires_membership("Administrators")
def config_verify():
    ensure_settings()

    return dict()


@auth.requires_membership("Administrators")
def config_verify_auto():
    ensure_settings()

    return dict()


@auth.requires_membership("Administrators")
def changepassword():
    ensure_settings()

    form = SQLFORM.factory(
    #Field('old_password', 'password'),
    Field('new_password', 'password', requires=[IS_NOT_EMPTY(),IS_STRONG(min=6, special=1, upper=1,
        error_message='minimum 6 characters, and at least 1 uppercase character, 1 lower case character, and 1 special character')]),
    Field('confirm_new_password', 'password', requires=IS_EXPR('value==%s' % repr(request.vars.get('new_password', None)),
        error_message="Password fields don't match")),
    submit_button="Change Password").process()
    
    if form.accepted:
        confirm_pw = request.vars.get('confirm_new_password')
        pw = request.vars.get('new_password', '')
        # admin_user = db(db.auth_user.username=='admin').select().first()
        if pw != "" and confirm_pw == pw:
            rows = db(db.auth_user.username == 'admin').select()
            for row in rows:
                id = row['id']
                # Set Web2py password
                db(db.auth_user.id==id).update( password=db.auth_user.password.validate(pw)[0] )
            response.flash = "Password Changed."
        else:
            response.flash = "Password not changed."
    elif form.errors:
        response.flash = "Unable to set new password"
    return dict(form=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def reload_modules():
    session.forget(response)
    import module_reload
    ret = module_reload.ReloadModules()
    #response.flash = "Python moudules reloaded..."
    return dict(msg="Modules Reloaded!")

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def reset_smc():
    ensure_settings()

    reset_smc_form = SQLFORM.factory(submit_button="Reset SMC App", _name="reset_smc_form").process(formname="reset_smc_form")
    
    kill_scheduler = SQLFORM.factory(submit_button="Kill Scheduler Process", _name="kill_scheduler").process(formname="kill_scheduler")

    reload_modules_form = SQLFORM.factory(submit_button="Reload Python Modules", _name="reload_modules").process(formname="reload_modules")
    
    ffmpeg_running=isFFMPEGRunning()
    if ffmpeg_running == "is NOT":
        ffmpeg_running = SPAN("is NOT", _style="color: red; font-weight: bold;")
    else:
        ffmpeg_running = SPAN("IS", _style="color: green; font-weight: bold;")

    if reset_smc_form.accepted:
        # Kill in VM
        cmd = "/usr/bin/nohup /bin/sleep 1; /usr/bin/killall -15 index.fcgi > /dev/null 2>&1 &"
        p = subprocess.Popen(cmd, shell=True, close_fds=True)
        ret = ""
        # p = subprocess.Popen("/bin/sleep 1 &; /usr/bin/killall -15 index.fcgi;", shell=True)
        # ret = p.wait()

        # Kill in docker (touch the wsgi file)
        # Find the web2py folder - Starts in the Controllers folder
        f = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        wsgi_file = os.path.join(f, "wsgihandler.py")
        os.system("touch " + wsgi_file)

        response.flash = "SMC App Reset" + str(ret)
    
    if kill_scheduler.accepted:
        # kill_process_videos_schedule_process()
        kill_all_workers()
        response.flash = "Scheduler process killed" # + str(ret)

    if reload_modules_form.accepted:
        #
        import module_reload
        module_reload.ReloadModules()

        # Make sure certain modules are init
        Canvas.Init()

        response.flash = "Modules reloaded!"
        pass
    
    return dict(reset_smc_form=reset_smc_form, ffmpeg_running=ffmpeg_running, kill_scheduler=kill_scheduler,
                reload_modules_form=reload_modules_form)


def kill_all_workers():
    #  ps ax |grep "web2py.py -K smc" | grep -v "grep" | awk '{print $1}' | xargs kill -9 $1
    # Kill the worker process
    app_name = request.application
    cmd = "ps ax |grep \"web2py.py -K " + app_name + "\" | grep -v \"grep\" | awk '{print $1}' | xargs kill -9 $1"
    p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    ret = p.wait()
    # ret = p.communicate()[0].decode()
    return ret


def kill_process_videos_schedule_process():
    # Kill the worker process
    app_name = request.application
    cmd = "pkill -9 -f 'web2py.py -K " + app_name + ":process_videos'"
    p = subprocess.Popen(cmd, shell=True, close_fds=True)
    ret = ""
    ret = p.wait()
    # ret = p.communicate()[0].decode()
    return ret


def isFFMPEGRunning():
    ret = "is NOT"
    cmd1 = ["/bin/ps ax | grep 'ffmpeg'"]
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
    out = p1.communicate()[0].decode()
    
    if 'ffmpeg -y' in out:
        ret = "IS"
    return ret


@auth.requires_membership("Administrators")
def ope():
    return dict(message="Welcome")


