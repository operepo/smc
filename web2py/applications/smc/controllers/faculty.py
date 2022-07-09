# -*- coding: utf-8 -*-


from ednet import AD
from ednet import Canvas
from ednet import Faculty
from ednet import Student

# Help shut up pylance warnings
if 1==2: from ..common import *

@auth.requires_membership('Faculty')
def changepassword():
    # See if this form has been disabled
    disabled = AppSettings.GetValue("disable_faculty_self_change_password", "False")
    # print(disabled)
    if disabled is True:
        form = "Feature disabled!"
        return dict(form=form)

    form = SQLFORM.factory(
        Field('old_password', 'password'),
        Field('new_password', 'password', requires=[IS_NOT_EMPTY(),IS_STRONG(min=6, special=1, upper=1,
            error_message='minimum 6 characters, and at least 1 uppercase character, 1 lower case character, 1 number, and 1 special character')]),
        Field('confirm_new_password', 'password', requires=IS_EXPR('value==%s' % repr(request.vars.get('new_password', None)),
            error_message="Password fields don't match")),
        submit_button="Change Password").process()
    
    if (form.accepted):
        old_pw = request.vars.get('old_password')
        pw = request.vars.get('new_password', '')
        user_id = Faculty.GetUserIDFromUsername(auth.user.username)
        curr_password = Faculty.GetPassword(user_id)
        if (curr_password != old_pw):
            response.flash = "Incorrect old password!"
        elif (pw != ""):
            ret = Faculty.SetPassword(user_id, pw)
            if (ret != ""):
                response.flash = ret
            else:
                response.flash = "Password Changed."
    elif (form.errors):
        response.flash = "Unable to set new password"
    return dict(form=form)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def index(): return dict(message="hello from faculty.py")


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def manage_students():
    
    # Set back link
    session.back = URL(args=request.args, vars=request.get_vars, host=True)
    
    #SQLFORM.factory(Field('item_cat'),widget=SQLFORM.widget.autocomplete(request, db.cat.name))
    #SQLFORM.factory(Field('item_cat',db.cat),widget=SQLFORM.widget.autocomplete(request, db.cat.name, id_field=db.cat.id) )
    #id_field=db.student_info.user_id
    choose_student_form = SQLFORM.factory(
        Field('student_name', 'string', widget=SQLFORM.widgets.autocomplete(request, db.student_info.student_name, limitby=(0,10), min_length=1 )), submit_button="Find" )
    
    query = db.student_info
    
    db.student_info.import_classes.readable=False
    db.student_info.student_ad_quota.readable=False
    db.student_info.student_canvas_quota.readable=False
    db.student_info.account_enabled.readable=False
    db.student_info.student_password.readable=False
    db.student_info.student_guid.readable=False
    db.student_info.sheet_name.readable=False
    db.student_info.id.readable=False
    #db.student_info.account_id.readable=False
    db.student_info.user_id.label = "ID"
    db.student_info.account_id.label = "User Name"
    db.student_info.additional_fields.readable=False
    
    fields = (db.student_info.user_id,
              db.student_info.account_id,
              db.student_info.student_name,
              db.student_info.import_classes,
              db.student_info.student_ad_quota,
              #db.student_info.student_canvas_quota,
              db.student_info.account_enabled,
              db.student_info.account_added_on,
              db.student_info.account_updated_on,
              #db.student_info.account_id,
              db.student_info.ad_last_login,
              )
    maxtextlengths = {'student_info.account_added_on': 24, 'student_info.account_updated_on': 24, 'student_info.ad_last_login': 24}
    
    links = [
             #dict(header=T('Last AD Logon'),body=lambda row: Student.GetLastADLoginTime(row.user_id ) ),
             dict(header=T('Enrollment'),body=lambda row: A(Student.GetEnrolledClassesString(row.user_id), _href=URL('faculty', 'student_enrollment', args=[row.user_id], user_signature=True)) ),
             #dict(header=T('Canvas Quota'),body=lambda row: A(GetDisplaySize(row.student_canvas_quota), _href=URL('faculty', 'student_canvas_quota', args=[row.user_id])) ),
             dict(header=T('AD Quota'),body=lambda row: A(GetDisplaySize(row.student_ad_quota), _href=URL('faculty', 'student_ad_quota', args=[row.user_id])) ),
             dict(header=T('Account Enabled'),body=lambda row: A(row.account_enabled, _href=URL('faculty', 'student_toggle_enabled', args=[row.user_id])) ),
             dict(header=T('Change Password'),body=lambda row: A('Change Password', _href=URL('faculty', 'student_change_password', args=[row.user_id])) ),
             dict(header=T('Upload Media***'),body=lambda row: A(GetUploadMediaStatus(row.account_id), _href=URL('faculty', 'student_toggle_upload_media', args=[row.user_id, row.account_id])) ),
             ]
    
    user_grid = SQLFORM.grid(query, fields=fields, orderby=db.student_info.student_name,
                             searchable=True, create=False, deletable=False, paginate=50,
                             csv=False, details=False, editable=False,
                             links=links, links_placement='right', links_in_grid=True,
                             maxtextlengths=maxtextlengths
                             )
    
    return dict(choose_student_form=choose_student_form, user_grid=user_grid)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def manage_faculty():
    
    # Set back link
    session.back = URL(args=request.args, vars=request.get_vars, host=True)
    
    #SQLFORM.factory(Field('item_cat'),widget=SQLFORM.widget.autocomplete(request, db.cat.name))
    #SQLFORM.factory(Field('item_cat',db.cat),widget=SQLFORM.widget.autocomplete(request, db.cat.name, id_field=db.cat.id) )
    #id_field=db.student_info.user_id
    choose_faculty_form = SQLFORM.factory(
        Field('faculty_name', 'string', widget=SQLFORM.widgets.autocomplete(request, db.faculty_info.faculty_name, limitby=(0,10), min_length=1 )), submit_button="Find" )
    
    query = db.faculty_info
    
    db.faculty_info.import_classes.readable=False
    db.faculty_info.faculty_ad_quota.readable=False
    db.faculty_info.faculty_canvas_quota.readable=False
    db.faculty_info.account_enabled.readable=False
    db.faculty_info.faculty_password.readable=False
    db.faculty_info.faculty_guid.readable=False
    db.faculty_info.sheet_name.readable=False
    db.faculty_info.id.readable=False
    #db.faculty_info.account_id.readable=False
    db.faculty_info.user_id.label = "ID"
    db.faculty_info.account_id.label = "User Name"
    db.faculty_info.additional_fields.readable=False
    
    fields = (db.faculty_info.user_id,
              db.faculty_info.account_id,
              db.faculty_info.faculty_name,
              db.faculty_info.import_classes,
              db.faculty_info.faculty_ad_quota,
              #db.faculty_info.faculty_canvas_quota,
              db.faculty_info.account_enabled,
              db.faculty_info.account_added_on,
              db.faculty_info.account_updated_on,
              #db.faculty_info.account_id,
              db.faculty_info.ad_last_login,
              )
    maxtextlengths = {'faculty_info.account_added_on': 24, 'faculty_info.account_updated_on': 24, 'faculty_info.ad_last_login': 24}
    
    links = [
             #dict(header=T('Last AD Logon'),body=lambda row: Faculty.GetLastADLoginTime(row.user_id ) ),
             dict(header=T('Enrollment'),body=lambda row: A(Faculty.GetEnrolledClassesString(row.user_id), _href=URL('faculty', 'faculty_enrollment', args=[row.user_id], user_signature=True)) ),
             #dict(header=T('Canvas Quota'),body=lambda row: A(GetDisplaySize(row.faculty_canvas_quota), _href=URL('faculty', 'faculty_canvas_quota', args=[row.user_id])) ),
             dict(header=T('AD Quota'),body=lambda row: A(GetDisplaySize(row.faculty_ad_quota), _href=URL('faculty', 'faculty_ad_quota', args=[row.user_id])) ),
             dict(header=T('Account Enabled'),body=lambda row: A(row.account_enabled, _href=URL('faculty', 'faculty_toggle_enabled', args=[row.user_id])) ),
             dict(header=T('Change Password'),body=lambda row: A('Change Password', _href=URL('faculty', 'faculty_change_password', args=[row.user_id])) ),
             dict(header=T('Allow Import'),body=lambda row: A(GetImportPermissionStatus(row.account_id), _href=URL('faculty', 'faculty_toggle_import', args=[row.user_id, row.account_id])) ),
             dict(header=T('Allow Admin'),body=lambda row: A(GetAdminPermissionStatus(row.account_id), _href=URL('faculty', 'faculty_toggle_admin', args=[row.user_id, row.account_id])) ),
             dict(header=T('Allow Laptop Logs'),body=lambda row: A(GetLaptopLogsPermissionStatus(row.account_id), _href=URL('faculty', 'faculty_toggle_laptop_logs', args=[row.user_id, row.account_id])) ),
             ]
    
    user_grid = SQLFORM.grid(query, fields=fields, orderby=db.faculty_info.faculty_name,
                             searchable=True, create=False, deletable=False, paginate=50,
                             csv=False, details=False, editable=False,
                             links=links, links_placement='right', links_in_grid=True,
                             maxtextlengths=maxtextlengths
                             )
    
    return dict(choose_faculty_form=choose_faculty_form, user_grid=user_grid)

def UpdateLastADLogin():
    ret = ""
    # Update the last login value for all users (students and faculty)
    if (AD.ConnectAD() != True):
        ret = "[AD Disabled]" + AD.GetErrorString()
        return ret
    
    # Grab list of students
    rows = db(db.student_info).select(db.student_info.user_id)
    for row in rows:
        #ret += "UID: " + row.user_id
        ll = Student.GetLastADLoginTime(row.user_id)
        #if (ll == None):
        #    ret += "None"
        #else:
        #    ret += str(ll)
        db(db.student_info.user_id==row.user_id).update(ad_last_login=ll)
        pass
    db.commit()
    
    # Grab a list of faculty
    rows = db(db.faculty_info).select(db.faculty_info.user_id)
    for row in rows:
        #ret += "UID: " + row.user_id
        ll = Faculty.GetLastADLoginTime(row.user_id)
        #if (ll == None):
        #    ret += "None"
        #else:
        #    ret += str(ll)
        db(db.faculty_info.user_id==row.user_id).update(ad_last_login=ll)
        pass
    db.commit()
    
    rows=None
    ad_errors = AD.GetErrorString()
    ret = "Done."
    return locals()

def GetDisplaySize(size):
    ret = "0 Meg"
    record = db(db.quota_sizes.int_size==size).select().first()
    if (record != None):
        ret = record['display_size']
    return ret

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_change_password():
    student_id = request.args(0)
    if (student_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    default_pw_form = SQLFORM.factory(submit_button="Set Default Password", _name="default_pw_form").process(formname="default_pw_form")
    
    custom_pw_form = SQLFORM.factory(
        Field('new_password', 'password', requires=[IS_NOT_EMPTY(),IS_STRONG(min=6, special=1, upper=1,
            error_message='minimum 6 characters, and at least 1 uppercase character, 1 lower case character, and 1 special character')]),
        Field('confirm_new_password', 'password', requires=IS_EXPR('value==%s' % repr(request.vars.get('new_password', None)),
                error_message="Password fields don't match")),
        submit_button="Set New Password", _name="custom_pw_form").process(formname="custom_pw_form")
    
    if (default_pw_form.accepted):
        new_pw = AppSettings.GetValue('student_password_pattern', 'SID<user_id>!')
        # Replace the possible values in this string with real info
        new_pw = Student.process_config_params(student_id, new_pw, is_username=False, row=None)
        #new_pw = new_pw.replace('<user_id>', student_id)
        msg = Student.SetPassword(student_id, new_pw)
        if msg == "":
            response.flash = "Default Password Set!"
        else:
            response.flash = msg
    
    if (custom_pw_form.accepted):
        pw = request.vars.get('new_password', '')
        if (pw != ""):
            ret = Student.SetPassword(student_id, pw)
            if (ret != ""):
                response.flash = ret
            else:
                response.flash = "Password Changed."
    elif (custom_pw_form.errors):
        response.flash = "Unable to set new password"
    
    return dict(default_pw_form=default_pw_form, custom_pw_form=custom_pw_form, current_user=current_user)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_change_password():
    faculty_id = request.args(0)
    if (faculty_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    default_pw_form = SQLFORM.factory(submit_button="Set Default Password", _name="default_pw_form").process(formname="default_pw_form")
    
    custom_pw_form = SQLFORM.factory(
        Field('new_password', 'password', requires=[IS_NOT_EMPTY(),IS_STRONG(min=6, special=1, upper=1,
            error_message='minimum 6 characters, and at least 1 uppercase character, 1 lower case character, and 1 special character')]),
        Field('confirm_new_password', 'password', requires=IS_EXPR('value==%s' % repr(request.vars.get('new_password', None)),
                error_message="Password fields don't match")),
        submit_button="Set New Password", _name="custom_pw_form").process(formname="custom_pw_form")
    
    if (default_pw_form.accepted):
        new_pw = AppSettings.GetValue('faculty_password_pattern', 'FID<user_id>#')
        # Replace the possible values in this string with real info
        new_pw = Faculty.process_config_params(faculty_id, new_pw, is_username=False, row=None)
        msg = Faculty.SetPassword(faculty_id, new_pw)
        if msg == "":
            response.flash = "Default Password Set!"
        else:
            response.flash = msg
            
    if (custom_pw_form.accepted):
        pw = request.vars.get('new_password', '')
        if (pw != ""):
            ret = Faculty.SetPassword(faculty_id, pw)
            if (ret != ""):
                response.flash = ret
            else:
                response.flash = "Password Changed."
    elif (custom_pw_form.errors):
        response.flash = "Unable to set new password"
    
    return dict(default_pw_form=default_pw_form, custom_pw_form=custom_pw_form, current_user=current_user)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_toggle_enabled():
    student_id = request.args(0)
    if student_id == None:
        if session.back:
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    status_action = "Change Status"
    
    student = db(db.student_info.user_id==student_id).select().first()
    if (student == None):
        message = 'Invalid Student!'
    else:
        if (student.account_enabled == True):
            # Disable
            r = Student.DisableAccount(student_id)
            if r != "":
                r = " - ERROR trying to disable account - most likely couldn't find LDAP object. Make sure AD Student Cn is configured correctly in  Admin -> Configure App -> Student Settings  (missing cn=<program>)??"  + r
            message = "Account disabled. " + r
            status_action = 'Disable Account'
        else:
            # Enable
            r = Student.EnableAccount(student_id)
            if r != "":
                r = " - ERROR trying to enable account - most likely couldn't find LDAP object. Make sure AD Student Cn is configured correctly in  Admin -> Configure App -> Student Settings  (missing cn=<program>)??"  + r
            message = "Account enabled. " + r
            status_action = 'Enable Account'
    return dict(message=message, current_user=current_user, status_action=status_action)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_toggle_upload_media():
    student_id = request.args(0)
    account_id = request.args(1)
    if (student_id == None or account_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    status_action = "Change Status"
    auth = current.auth # Grab the current auth object
    
    # Add to the group
    if (auth.has_membership(role='Media Upload', user_id=account_id) == True):
        status_action = "Removing Media Upload Rights"        
        auth.del_membership(auth.id_group(role='Media Upload'), user_id=account_id)
    else:
        status_action = "Adding Media Upload Rights"
        auth.add_membership('Media Upload', user_id=account_id)
    message = status_action
    return dict(message=message, current_user=current_user, status_action=status_action)

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def GetUploadMediaStatus(account_id):
    ret = "True"
    auth = current.auth # Grab the current auth object
    
    if (auth.has_membership(role='Media Upload', user_id=account_id) == True):
        ret = "True"
    else:
        ret = "False"
    
    return ret

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_toggle_import():
    faculty_id = request.args(0)
    account_id = request.args(1)
    if (faculty_id == None or account_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    status_action = "Change Status"
    auth = current.auth # Grab the current auth object
    
    # Add to the group
    if (auth.has_membership(role='Import', user_id=account_id) == True):
        status_action = "Removing Import Rights"        
        auth.del_membership(auth.id_group(role='Import'), user_id=account_id)
    else:
        status_action = "Adding Import Rights"
        auth.add_membership('Import', user_id=account_id)
    message = status_action
    return dict(message=message, current_user=current_user, status_action=status_action)

@auth.requires(auth.has_membership('Administrators'))
def faculty_toggle_admin():
    faculty_id = request.args(0)
    account_id = request.args(1)
    if (faculty_id == None or account_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    status_action = "Change Status"
    auth = current.auth # Grab the current auth object
    
    # Add to the group
    if (auth.has_membership(role='Administrators', user_id=account_id) == True):
        status_action = "Removing Admin Rights"        
        auth.del_membership(auth.id_group(role='Administrators'), user_id=account_id)
    else:
        status_action = "Adding Admin Rights"
        auth.add_membership('Administrators', user_id=account_id)
    message = status_action
    return dict(message=message, current_user=current_user, status_action=status_action)

@auth.requires(auth.has_membership('Administrators'))
def faculty_toggle_laptop_logs():
    faculty_id = request.args(0)
    account_id = request.args(1)
    if (faculty_id == None or account_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    status_action = "Change Status"
    auth = current.auth # Grab the current auth object
    
    # Add to the group
    if (auth.has_membership(role='Laptop Logs', user_id=account_id) == True):
        status_action = "Removing Laptop Log Rights"        
        auth.del_membership(auth.id_group(role='Laptop Logs'), user_id=account_id)
    else:
        status_action = "Adding Laptop Log Rights"
        auth.add_membership('Laptop Logs', user_id=account_id)
    message = status_action
    return dict(message=message, current_user=current_user, status_action=status_action)


@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def GetLaptopLogsPermissionStatus(account_id):
    ret = "True"
    auth = current.auth # Grab the current auth object
    
    if (auth.has_membership(role='Laptop Logs', user_id=account_id) == True):
        ret = "True"
    else:
        ret = "False"
    
    return ret


@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def GetAdminPermissionStatus(account_id):
    ret = "True"
    auth = current.auth # Grab the current auth object
    
    if (auth.has_membership(role='Administrators', user_id=account_id) == True):
        ret = "True"
    else:
        ret = "False"
    
    return ret


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def GetImportPermissionStatus(account_id):
    ret = "True"
    auth = current.auth # Grab the current auth object
    
    if (auth.has_membership(role='Import', user_id=account_id) == True):
        ret = "True"
    else:
        ret = "False"
    
    return ret

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_toggle_enabled():
    faculty_id = request.args(0)
    if (faculty_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    status_action = "Change Status"
    
    faculty = db(db.faculty_info.user_id==faculty_id).select().first()
    if (faculty == None):
        message = 'Invalid Faculty!'
    else:
        if (faculty.account_enabled == True):
            # Disable
            Faculty.DisableAccount(faculty_id)
            message = "Account disabled."
            #message += AD.GetErrorString()
            status_action='Disable Account'
        else:
            # Enable
            Faculty.EnableAccount(faculty_id)
            message = "Account enabled."
            status_action='Enable Account'
    #message += Faculty.GetPassword(faculty_id)
    return dict(message=message, current_user=current_user, status_action=status_action)

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_ad_quota():
    student_id = request.args(0)
    if (student_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    row = db(db.student_info.user_id==student_id).select().first()
    form = SQLFORM(db.student_info, row, showid=False,
                   fields=["student_ad_quota"]).process()
    
    if (form.accepted):
        # Saved
        quota = request.vars.get('student_ad_quota', '0')
        result = AD.SetDriveQuota(current_user, quota)
        msg = "Settings Saved!"
        if (result is False and len(AD._errors) > 0):
            msg += AD.GetErrorString()
        response.flash = msg
        
    
    return dict(form=form, current_user=current_user)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_ad_quota():
    faculty_id = request.args(0)
    if (faculty_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    row = db(db.faculty_info.user_id==faculty_id).select().first()
    form = SQLFORM(db.faculty_info, row, showid=False,
                   fields=["faculty_ad_quota"]).process()
    
    if (form.accepted):
        # Saved
        quota = request.vars.get('faculty_ad_quota', '0')
        AD.SetDriveQuota(current_user, quota)
        msg = "Settings Saved!"
        if (len(AD._errors) > 0):
            msg += AD.GetErrorString()
        response.flash = msg
        
    
    return dict(form=form, current_user=current_user)

@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_canvas_quota():
    student_id = request.args(0)
    if (student_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    row = db(db.student_info.user_id==student_id).select().first()
    form = SQLFORM(db.student_info, row, showid=False,
                   fields=["student_canvas_quota"]).process()
    
    if (form.accepted):
        # Saved
        quota = request.vars.get('student_canvas_quota', '1')
        Canvas.SetQuota(current_user, quota)
        msg = "Settings Saved!"
        if (len(Canvas._errors) > 0):
            msg += Canvas.GetErrorString()
        response.flash = msg
        
    
    return dict(form=form, current_user=current_user)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_canvas_quota():
    faculty_id = request.args(0)
    if (faculty_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    row = db(db.faculty_info.user_id==faculty_id).select().first()
    form = SQLFORM(db.faculty_info, row, showid=False,
                   fields=["faculty_canvas_quota"]).process()
    
    if (form.accepted):
        # Saved
        quota = request.vars.get('faculty_canvas_quota', '1')
        Canvas.SetQuota(current_user, quota)
        msg = "Settings Saved!"
        if (len(Canvas._errors) > 0):
            msg += Canvas.GetErrorString()
        response.flash = msg
        
    
    return dict(form=form, current_user=current_user)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def student_enrollment():
    student_id = request.args(0)
    if (student_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_student'))
    
    current_user = Student.GetUsername(student_id)
    
    user = db(db.student_info.user_id==student_id).select().first()
    query=None
    if (user != None):
        query = (db.student_enrollment.parent_id==user['id'])
    
    fields = (db.student_enrollment.course_code,
              db.student_enrollment.enrollment_status,
              db.student_enrollment.enrolled_on,
              )
    
    #links = [dict(header=T('Enrollment'),body=lambda row: A(Student.GetEnrolledClassesString(row.user_id), _href=URL('faculty', 'student_enrollment', args=[row.user_id], user_signature=True)) ),
    #         ]
    
    form = SQLFORM.grid(query, fields=fields, orderby=db.student_enrollment.course_code,
                        searchable=False, create=False, deletable=False, paginate=50,
                        csv=False, details=False, editable=False,
                        links=None, links_placement='right', links_in_grid=True)
    
    
    return dict(form=form, current_user=current_user)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_enrollment():
    faculty_id = request.args(0)
    if (faculty_id == None):
        if (session.back):
            redirect(session.back)
        else:
            redirect(URL('faculty', 'manage_faculty'))
    
    current_user = Faculty.GetUsername(faculty_id)
    
    user = db(db.faculty_info.user_id==faculty_id).select().first()
    query=None
    if (user != None):
        query = (db.faculty_enrollment.parent_id==user['id'])
    
    fields = (db.faculty_enrollment.course_code,
              db.faculty_enrollment.enrollment_status,
              db.faculty_enrollment.enrolled_on,
              )
    
    #links = [dict(header=T('Enrollment'),body=lambda row: A(Student.GetEnrolledClassesString(row.user_id), _href=URL('faculty', 'student_enrollment', args=[row.user_id], user_signature=True)) ),
    #         ]
    
    form = SQLFORM.grid(query, fields=fields, orderby=db.faculty_enrollment.course_code,
                        searchable=False, create=False, deletable=False, paginate=50,
                        csv=False, details=False, editable=False,
                        links=None, links_placement='right', links_in_grid=True)
    
    
    return dict(form=form, current_user=current_user)


@auth.requires(auth.has_membership('Faculty') or auth.has_membership('Administrators'))
def create_new_student():
    return dict()

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def create_new_faculty():
    return dict()


@auth.requires(auth.has_membership('Laptop Logs') or auth.has_membership('Administrators'))
def laptop_logs():
    laptops = None

    # Get a list of credentialed laptops

    query = db.ope_laptops

    db.ope_laptops.id.readable=False
    db.ope_laptops.auth_key.readable=False
    db.ope_laptops.admin_password_status.readable=False
    db.ope_laptops.extra_info.readable=False
    db.ope_laptops.admin_user.readable=False
    db.ope_laptops.credentialed_by_user.readable=False
    db.ope_laptops.archived.readable=False

    maxtextlengths={"Screen Shots": 50,}
    links = [
            dict(header=T(''),
                body=lambda row: SPAN(
                    A("[Screen Shots]", _style="white-space: nowrap;", _href=URL('faculty', 'ope_laptop_screenshots', args=[row.id])),
                    A("[Log Files]", _style="white-space: nowrap;", _href=URL('faculty', 'ope_laptop_logs', args=[row.id])),
                    A("[Details]", _style="white-space: nowrap;", _href=URL('faculty', 'ope_laptop_details', args=[row.id])),
                    )
                ),

            ]
    
    laptops = SQLFORM.grid(query, orderby=db.ope_laptops.current_student,
        searchable=True, create=False, deletable=False, paginate=50,
        csv=False, details=False, editable=False,
        links=links, links_placement='left', links_in_grid=True,
        maxtextlengths=maxtextlengths
        )


    return dict(laptops=laptops)