from gluon import *
from gluon import current

# import applications.smc.modules.xlrd
# from .. import xlrd
import xlrd
import time
from datetime import timedelta

from ednet.util import Util
from ednet.appsettings import AppSettings
from ednet.w2py import W2Py
from ednet.ad import AD
from ednet.canvas import Canvas


class Student:
    def __init__(self):
        pass
    
    @staticmethod
    def ProcessExcelFile(excel_file):
        out = DIV(Student.ClearImportQueue())
        db = current.db  # Grab the current db object
        
        wbook = xlrd.open_workbook(excel_file)
        for sheet in wbook.sheets():
            out.append(DIV("Processing Sheet: " + sheet.name))
            out.append(DIV("Processing Enabled Students."))
            student_account_enabled = True  # status 1 = active, 0 = inactive
            for row in range(sheet.nrows):
                if Util.GetCellValue(sheet, row, 0).upper() == "USER ID":
                    out.append(DIV("Skipping Header Row."))
                    continue  # should be header, skip this line
                if Util.GetCellValue(sheet, row, 0).upper() == "DOC":
                    out.append(DIV("Skipping Header Row."))
                    continue  # should be header, skip this line
                if Util.GetCellValue(sheet, row, 0).startswith("**"):
                    # Found stars, switch state
                    student_account_enabled = False
                    out.append(DIV("Processing Disabled Students."))
                    continue  # divider row, skip this line
                if Util.GetCellValue(sheet, row, 0) == "":
                    # out.append(DIV("Skipping Blank Row."))
                    continue  # No data, skip this line
                # if (Util.GetCellValue(sheet, row, 0).isdigit() != True):
                #    out.append(DIV("Skipping non numeric DOC Number: " + Util.GetCellValue(sheet, row, 0)))
                #    continue # No data, skip this line

                # Grab info from cells
                user_id = Util.GetCellValue(sheet, row, 0)
                student_name = Util.GetCellValue(sheet, row, 1)
                student_password = Util.GetCellValue(sheet, row, 2)
                import_classes = Util.GetCellValue(sheet, row, 3)
                program = Util.GetCellValue(sheet, row, 4)
                additional_fields = ""
                if sheet.ncols > 5:
                    additional_fields = Util.GetJSONFromCellRange(sheet, row, 5, sheet.ncols)

                sheet_name = sheet.name
                student_guid = None
                account_enabled = student_account_enabled
                account_added_on = time.strftime("%c")
                account_updated_on = time.strftime("%c")

                db.student_import_queue.insert(
                        user_id=user_id,
                        student_name=student_name,
                        student_password=student_password,
                        import_classes=import_classes,
                        program=program,
                        additional_fields=additional_fields,
                        sheet_name=sheet_name,
                        student_guid=student_guid,
                        account_enabled=account_enabled,
                        account_added_on=account_added_on,
                        account_updated_on=account_updated_on
                    )
                db.commit()
                out.append(DIV("Found: " + user_id + " - " + student_name))

                # values = []
                # for col in range(sheet.ncols):
                #    values.append(str(sheet.cell(row, col).value))
                # out += ','.join(values)
        out.append(DIV("Processing Complete", _style='font-weight: bold; font-size: 18px; color: red;'))
        return out

    @staticmethod
    def ClearImportQueue():
        db = current.db # Grab the current db object
        # Make sure that the import table is empty
        db.executesql('DELETE FROM student_import_queue;')
        return "Student Import Queue Cleared."

    @staticmethod
    def CreateW2PyAccounts(sheet_name, override_password=False, override_current_quota=False):
        # Create web2py accounts for this student
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object
        count = 0
    
        # Get the users to import
        rows = db(db.student_import_queue.sheet_name == sheet_name).select()
        for row in rows:
            count += 1
            
            # Gather info for this user
            user_name = Student.GetUsername(row.user_id)
            password = Student.GetPassword(row.user_id, row.student_password, override_password)
            user_email = Student.GetEmail(row.user_id)
            (first_name, last_name) = Util.ParseName(row.student_name)
            user_ad_quota = Student.GetADQuota(row.user_id, override_current_quota)
            user_canvas_quota = Student.GetCanvasQuota(row.user_id, override_current_quota)
            
            W2Py.CreateW2PStudentUser(user_name, password, user_email, first_name, last_name, user_ad_quota,
                                      user_canvas_quota, row)
        return count

    @staticmethod
    def GetLastADLoginTime(student_id):
        ret = ""
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object
        
        user_name = Student.GetUsername(student_id)
        
        # AD - Disable
        user_dn = Student.GetAD_DN(user_name, Student.GetProgram(student_id))
        
        ret = AD.GetLastLoginTime(user_dn)
        return ret
    
    @staticmethod
    def DisableAccount(student_id):
        ret = ""
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object
        
        user_name = Student.GetUsername(student_id)
        
        pw = "J#jsa3#31" + str(time.time())
        
        Student.SetPassword(student_id, pw, False)
        
        user_dn = Student.GetAD_DN(user_name, Student.GetProgram(student_id))
        r = AD.DisableUser(user_dn)
        
        # Update the database to reflect the change
        db(db.student_info.user_id == student_id).update(account_enabled=False)
        if r is False:
            ret = "ERROR disabling account - " + AD.GetErrorString()
        return ret
    
    @staticmethod
    def EnableAccount(student_id):
        ret = ""
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object
        
        user_name = Student.GetUsername(student_id)
        
        pw = Student.GetPassword(student_id)
        
        Student.SetPassword(student_id, pw)
        
        # AD - Disable
        user_dn = Student.GetAD_DN(user_name, Student.GetProgram(student_id))
        r = AD.EnableUser(user_dn)
        
        # Update the database to reflect the change
        db(db.student_info.user_id == student_id).update(account_enabled=True)

        if r is False:
            ret = "ERROR disabling account - " + AD.GetErrorString()
        return ret
    
    @staticmethod
    def GetUserIDFromUsername(user_name):
        ret = ""
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object
        
        rows = db(db.auth_user.username == user_name).select()
        for row in rows:
            students = db(db.student_info.account_id == row.id).select()
            for student in students:
                ret = student.user_id
        return ret

    @staticmethod
    def process_config_params(student_id, txt, is_username=False):
        db = current.db  # Grab the current db object
        ret = ""

        # Patters = first_name, last_name, first_name_first_letter, first_name_last_letter,
        # last_name_first_letter, last_name_last_letter
        first_name = ""
        last_name = ""

        first_name_first_letter = ""
        first_name_last_letter = ""
        last_name_first_letter = ""
        last_name_last_letter = ""

        user = db(db.student_info.user_id == student_id).select(db.student_info.student_name).first()
        if user is not None:
            (first_name, last_name) = Util.ParseName(user.student_name)

        if first_name != "":
            first_name_first_letter = first_name[:1]
            first_name_last_letter = first_name[-1:]
        if last_name != "":
            last_name_first_letter = last_name[:1]
            last_name_last_letter = last_name[-1:]

        ret = txt.replace('<user_id>', student_id)
        ret = ret.replace('<first_name>', first_name)
        ret = ret.replace('<first_name_first_letter>', first_name_first_letter)
        ret = ret.replace('<first_name_last_letter>', first_name_last_letter)
        ret = ret.replace('<last_name>', last_name)
        ret = ret.replace('<last_name_first_letter>', last_name_first_letter)
        ret = ret.replace('<last_name_last_letter>', last_name_last_letter)

        # Make sure we don't call this if it is coming FROM the username function
        if is_username is not True:
            user_name = Student.GetUsername(student_id)
            ret = ret.replace('<user_name>', user_name)
            ret = ret.replace('%username%', user_name)

        return str(ret)
    
    @staticmethod
    def GetUsername(student_id):
        ret = ""

        pattern = AppSettings.GetValue('student_id_pattern', '<user_id>')
        ret = Student.process_config_params(student_id, pattern, is_username=True)

        return str(ret)
    
    @staticmethod
    def GetProgram(student_id):
        db = current.db
        ret = ""
        user = db(db.student_info.user_id == student_id).select(db.student_info.program).first()
        if user is not None:
            ret = user.program
        if ret is None:
            ret = ""
        return ret

    @staticmethod
    def GetPassword(student_id, import_password="", override_password=False):
        db = current.db
        # Get current password if student exists so we don't
        # reset it if the student has already changed it unless override_password == True
        ret = import_password
        if override_password is not True:
            rows = db(db.student_info.user_id == student_id).select(db.student_info.student_password)
            for row in rows:
                ret = row.student_password
        # If password isn't set, use the pattern and set the default pw
        # Default - add SID to beginning and ! to end (e.g. SID1888182!)
        if ret == "":
            pattern = AppSettings.GetValue('student_password_pattern', 'SID<user_id>!')
            ret = Student.process_config_params(student_id, pattern)
        return str(ret)

    @staticmethod
    def SetPassword(student_id, new_password, update_db=True):
        db = current.db
        ret = ""
        
        if student_id == "" or new_password == "":
            return "Can't set empty password!"
        
        if len(new_password) < 6:
            return "Can't set password - Too short!"
        
        # Set AD password
        user_name = Student.GetUsername(student_id)
        if AD.Connect() is True:
            user_dn = Student.GetAD_DN(user_name, Student.GetProgram(student_id))
            if AD.SetPassword(user_dn, new_password) is not True:
                return "<b>Error setting AD password:</b> " + AD.GetErrorString()
        else:
            # Don't set ad password if ad isn't enabled
            pass
            
        # Set Canvas password
        if Canvas.SetPassword(user_name, new_password) is not True:
            return "<b>Error setting Canvas password:</b> " + Canvas.GetErrorString()
        
        if W2Py.SetStudentPassword(user_name, new_password, update_db) is not True:
            return "<b>Error setting system password</b>"
        
        return ret
    
    @staticmethod
    def GetEmail(student_id):
        # Default -Prepend user_name @domain.com (e.g. s1888182@correctionsed.com)
        pattern = AppSettings.GetValue('student_email_pattern', '<user_name>@correctionsed.com')
        ret = Student.process_config_params(student_id, pattern)
        return str(ret)
    
    @staticmethod
    def GetHomeDirectory(student_id):
        # Default - ""  #  \\files\students\%username%
        pattern = AppSettings.GetValue('ad_student_home_directory', '')
        ret = Student.process_config_params(student_id, pattern)
        return str(ret)

    @staticmethod
    def GetHomeDrive(student_id):
        # Default - nothing (off)
        pattern = AppSettings.GetValue('ad_student_home_drive', '')
        ret = Student.process_config_params(student_id, pattern)
        return str(ret)

    @staticmethod
    def GetLoginScriptPath(student_id):
        # Default - nothing (off)
        pattern = AppSettings.GetValue('ad_student_login_script_path', '')
        ret = Student.process_config_params(student_id, pattern)
        return str(ret)

    @staticmethod
    def GetProfilePath(student_id):
        # Default - nothing (off)
        pattern = AppSettings.GetValue('ad_student_profile_directory', '')
        ret = Student.process_config_params(student_id, pattern)
        return str(ret)

    @staticmethod
    def GetCanvasQuota(student_id, override_quota=False):
        # Lookup the quota for this user or use the default
        db = current.db

        # Start with a default value
        quota = AppSettings.GetValue('canvas_student_quota', '1048576')
        # Query for the student's value
        if override_quota is not True:
            rows = db(db.student_info.user_id == student_id).select(db.student_info.student_canvas_quota)
            for row in rows:
                quota = row.student_canvas_quota
        
        return str(quota)
    
    @staticmethod
    def GetADQuota(student_id, override_quota=False):
        # Lookup the quota for this user or use the default
        db = current.db

        # Start with a default value
        quota = AppSettings.GetValue('ad_student_home_directory_quota', '1048576')
        # Query for the student's value
        if override_quota is not True:
            rows = db(db.student_info.user_id == student_id).select(db.student_info.student_ad_quota)
            for row in rows:
                quota = row.student_ad_quota
        
        return str(quota)

    @staticmethod
    def QueueActiveDirectoryImports(sheet_name):
        db = current.db # Grab the current db object
        count = 0 # The number of entries processed

        ldap_enabled = AppSettings.GetValue('ad_import_enabled', False)
        if ldap_enabled is not True:
            return count

        # Clear the queue and add an entry in the queue table for
        # each student
        db.executesql('DELETE FROM student_ad_import_queue;')
        db.executesql('DELETE FROM student_ad_import_status;')

        rows = db(db.student_import_queue.sheet_name == sheet_name).select(db.student_import_queue.id)
        for row in rows:
            count += 1
            db.student_ad_import_queue.insert(student_import_queue=row['id'])

        return count

    @staticmethod
    def QueueCanvasImports(sheet_name):
        db = current.db  # Grab the current db object
        count = 0  # The number of entries processed

        canvas_enabled = AppSettings.GetValue('canvas_import_enabled', False)
        if canvas_enabled is not True:
            return count

        # Clear the queue and add an entry in the queue table for
        # each student
        db.executesql('DELETE FROM student_canvas_import_queue;')
        db.executesql('DELETE FROM student_canvas_import_status;')

        rows = db(db.student_import_queue.sheet_name == sheet_name).select(db.student_import_queue.id)
        for row in rows:
            count += 1
            db.student_canvas_import_queue.insert(student_import_queue=row['id'])

        return count

    @staticmethod
    def GetEnrolledClassesString(user_id):
        db = current.db  # Grab the current db object
        ret = ""
        
        classes = Student.GetEnrolledClasses(user_id)
        for c in classes:
            if ret != "":
                ret += ", "
            ret += c.course_code

        if ret == "":
            ret = "No Classes"
        return ret
    
    @staticmethod
    def GetEnrolledClasses(user_id):
        db = current.db  # Grab the current db object
        ret = []
        
        user = db(db.student_info.user_id == user_id).select().first()
        if user is not None:
            classes = user.student_enrollment.select()
            for c in classes:
                if c.enrollment_status == "active":
                    ret.append(c)
        return ret
    
    @staticmethod
    def GetAD_DN(user_name, program):
        ret = Student.GetAD_CN(program)
        ret = AD.GetDN(user_name, ret)
        
        return ret
    
    @staticmethod
    def GetAD_CN(program):
        ad_cn = AppSettings.GetValue('ad_student_cn', 'OU=Students,DC=ad,DC=correctionsed,DC=com')
        if program == "" or program is None:
            # If no program, take off the program OU
            ret = ad_cn.replace('ou=', 'OU=')
            ret = ret.replace('OU=<program>,', '')
        else:
            ret = ad_cn.replace('<program>', program)
        
        return ret
    
    @staticmethod
    def AddClass(user_id, class_name):
        db = current.db
        user = db(db.student_info.user_id == user_id).select().first()
        if user is not None:
            uid = user['id']
            if db((db.student_enrollment.parent_id==uid) & (db.student_enrollment.course_code == class_name))\
                    .select().first() is None:
                db.student_enrollment.insert(parent_id=uid, course_code=class_name,
                                             enrolled_on=time.strftime("%c"), enrollment_status='active')
    
    @staticmethod
    def ProcessADStudent():
        db = current.db  # Grab the current db object
        scheduler = current.scheduler
        ret = ""
        # AD.Close()

        ldap_enabled = AppSettings.GetValue('ad_import_enabled', False)
        if ldap_enabled is not True:
            return "Done! - LDAP Import Disabled"
        
        if AD.Connect() is not True:
            ret += "<b>Error connecting to Active Directory server</b><br/><font size=-4>"
            ret += AD.GetErrorString()
            ret += "</font><br/>Done!"
            return ret
        
        if AD.VerifyADSettings() is not True:
            ret += "<b>Error verifying AD settings</b><br/><font size=-4>"
            ret += AD.GetErrorString()
            ret += "</font><br/>Done!"
            return ret
        else:
            # If everything is good clear errors
            AD._errors = []
        
        # ad_student_cn = AppSettings.GetValue('ad_student_cn', 'OU=Students,DC=ad,DC=correctionsed,DC=com')
        ad_student_group_cn = AppSettings.GetValue('ad_student_group_cn',
                                                   'OU=StudentGroups,DC=ad,DC=correctionsed,DC=com')
        ad_student_group_dn = 'CN=Students,' + ad_student_group_cn
        
        # Ensure the student group exists
        if AD.CreateGroup(ad_student_group_dn) is not True:
            ret += "<b>Error creating students group:</b> " + str(ad_student_group_dn) + "<br />"
            ret += str(AD._errors)
        
        # Grab the first student off the queue
        rows = db(db.student_import_queue.id == db.student_ad_import_queue.student_import_queue)\
            .select(orderby=db.student_import_queue.account_enabled|db.student_import_queue.student_name,
                    limitby=(0, 1))
        
        for row in rows:
            # Pop the student off the queue
            db(db.student_ad_import_queue.id == row.student_ad_import_queue.id).delete()
            db.commit()
            # Get the student info
            # Get info for current student
            student_user_name = Student.GetUsername(row.student_import_queue.user_id)
            student_password = Student.GetPassword(row.student_import_queue.user_id,
                                                   row.student_import_queue.student_password)
            (student_first_name, student_last_name) = Util.ParseName(row.student_import_queue.student_name)
            student_email = Student.GetEmail(row.student_import_queue.user_id)
            student_display_name = row.student_import_queue.student_name + " (" + student_user_name + ")"
            student_user_id = row.student_import_queue.user_id
            student_home_directory = Student.GetHomeDirectory(row.student_import_queue.user_id)
            student_home_drive = Student.GetHomeDrive(row.student_import_queue.user_id)
            student_login_script_path = Student.GetLoginScriptPath(row.student_import_queue.user_id)
            student_profile_path = Student.GetProfilePath(row.student_import_queue.user_id)
            student_enabled = row.student_import_queue.account_enabled
            student_quota = Student.GetADQuota(row.student_import_queue.user_id)
            student_dn = Student.GetAD_DN(student_user_name, row.student_import_queue.program)
            student_cn = Student.GetAD_CN(row.student_import_queue.program)
            
            first_run = False
            fr = db(db.student_ad_import_status.user_id == row.student_import_queue.user_id).select().first()
            if fr is None:
                first_run = True
            db.student_ad_import_status.insert(user_id=row.student_import_queue.user_id)
            db.commit()

            # print("Student Info: ")
            # print(" -> User Name: " + str(student_user_name))
            # print(" -> Password: " + str(student_password))
            # print(" -> First Name: " + str(student_first_name))
            # print(" -> Last Name: " + str(student_last_name))
            # print(" -> Email: " + str(student_email))
            # print(" -> Display Name: " + str(student_display_name))
            # print(" -> ID: " + str(student_user_id))
            # print(" -> Home Dir: " + str(student_home_directory))
            # print(" -> Home Drive: " + str(student_home_drive))
            # print(" -> Login Script: " + str(student_login_script_path))
            # print(" -> Profile Path: " + str(student_profile_path))
            # print(" -> Enabled: " + str(student_enabled))
            # print(" -> Quota: " + str(student_quota))
            # print(" -> AD DN: " + str(student_dn))
            # print(" -> AD CN: " + str(student_cn))

            # Create the student
            if AD.CreateUser(student_user_name, student_cn) is not True:
                ret += "<b>Error creating students account:</b> " + str(student_user_name) +\
                       " - " + str(student_cn) + "<br />Done!"
                return ret
            db.commit()
            # Update user with current info
            if AD.UpdateUserInfo(student_dn, email_address=student_email, first_name=student_first_name,
                                 last_name=student_last_name, display_name=student_display_name,
                                 description="Student Account", id_number=student_user_name,
                                 home_drive_letter=student_home_drive, home_directory=student_home_directory,
                                 login_script=student_login_script_path, profile_path=student_profile_path,
                                 ts_allow_login='FALSE') is not True:
                ret += "<b>Error creating setting student information:</b> " + str(student_user_name) + "<br />"
            db.commit()
            # Set password
            if AD.SetPassword(student_dn, student_password) is not True:
                ret += "<b>Error setting password for user:</b> " + str(student_user_name) + "<br />"
            db.commit()
            # Add to the students group
            if AD.AddUserToGroup(student_dn, ad_student_group_dn) is not True:
                ret += "<b>Error adding user to students group:</b> " + str(student_user_name) + "<br />"
            db.commit()
            if student_enabled is True:
                AD.EnableUser(student_dn)
            else:
                AD.DisableUser(student_dn)
            db.commit()

            # Get the list of classes for this student
            if student_enabled is True:
                enroll_classes = row.student_import_queue.import_classes.split(',')
                for enroll_class in enroll_classes:
                    # Trim spaces
                    enroll_class = enroll_class.strip()

                    if enroll_class == '':
                        continue  # Skip empty class names
                    
                    Student.AddClass(row.student_import_queue.user_id, enroll_class)

                    class_dn = AD.GetDN(enroll_class, ad_student_group_cn)
                    if AD.GetLDAPObject(class_dn) is None:
                        # Class group doesn't exist, add it
                        if AD.CreateGroup(class_dn) is not True:
                            ret += "<b>Error creating class group:</b> " + str(enroll_class) + "<br />"

                    # Add student to the class group
                    if AD.AddUserToGroup(student_dn, class_dn) is not True:
                        ret += "<b>Error adding student to group:</b> " + str(student_user_name) + "/" +\
                               str(enroll_class) + "<br />"
            db.commit()
            # Setup physical home directory
            if student_enabled is True:
                # if (AD.CreateHomeDirectory(student_user_name, student_home_directory) != True):
                #    ret += "<b>Error creating home folder:</b> " + str(student_user_name) + "<br />"
                if first_run:
                    result = scheduler.queue_task('create_home_directory',
                                                  pvars=dict(user_name=student_user_name,
                                                             home_directory=student_home_directory),
                                                  timeout=1200, immediate=True, sync_output=5,
                                                  group_name="create_home_directory")
                if AD.SetDriveQuota(student_user_name, student_quota) is not True:
                    ret += "<b>Error setting quota for student:</b> " + str(student_user_name) + "<br />"
            db.commit()
            # Show errors
            if len(AD._errors) > 0:
                ret += AD.GetErrorString()
            
            ret += student_display_name  # + " (" + student_user_name + ")"
            if row.student_import_queue.account_enabled is True:
                ret += " - <span style='color: green; font-weight: bolder;'>Imported</span>"
            else:
                ret += " - <span style='color: red; font-weight: bolder;'>Disabled</span>"

        if ret == "":
            ret = "Done!"
        return ret
    
    @staticmethod
    def ProcessCanvasStudent():
        db = current.db  # Grab the current db object
        ret = ""
        log = ""
        Canvas.Close()
        
        if Canvas.Connect() is not True:
            ret += "<b>Error connecting to Canvas server</b><br/><font size=-4>"
            ret += Canvas.GetErrorString()
            ret += "</font><br/>"
            ret += "Done!"
            return ret
        
        if Canvas._canvas_enabled is not True:
            return "Done! - Canvas Import Disabled"

        # Pop one off the queue
        rows = db(db.student_import_queue.id == db.student_canvas_import_queue.student_import_queue)\
            .select(orderby=db.student_import_queue.account_enabled|db.student_import_queue.student_name,
                    limitby=(0, 1))
        for row in rows:
            # remove item from the queue
            db(db.student_canvas_import_queue.id == row.student_canvas_import_queue.id).delete()
            db.commit()
            # Get info for current student
            student_user_name = Student.GetUsername(row.student_import_queue.user_id)
            student_password = Student.GetPassword(row.student_import_queue.user_id,
                                                   row.student_import_queue.student_password)
            (student_first_name, student_last_name) = Util.ParseName(row.student_import_queue.student_name)
            student_email = Student.GetEmail(row.student_import_queue.user_id)
            student_display_name = row.student_import_queue.student_name
            student_user_id = row.student_import_queue.user_id
            student_enabled = row.student_import_queue.account_enabled
            db.commit()
            
            first_run = False
            fr = db(db.student_canvas_import_status.user_id == row.student_import_queue.user_id).select().first()
            if fr is None:
                # ret += " <span style='color: red; font-weight: bolder;'>FIRST RUN</span>"
                first_run = True
            db.student_canvas_import_status.insert(user_id=row.student_import_queue.user_id)
            db.commit()
            
            # Make sure the user exists
            canvas_user = Canvas.CreateUser(student_user_name, student_password, student_first_name,
                                            student_last_name, student_email)
            if canvas_user is None:
                ret += "<b>Error creating account:</b> " + str(student_user_name) + "<br />Done!"
                return ret
            
            # Mark all current classes as complete
            if first_run is True:
                enrollment_days_timedelta = timedelta(days=100)
                if student_enabled is not True:
                    # Disabled student, make sure to mark courses as completed
                    enrollment_days_timedelta = timedelta(days=-1)
                # print("Complete Classes " + student_user_name + " " + str(enrollment_days_timedelta))
                Canvas.CompleteAllClasses(student_user_name,
                                          enrollment_days_timedelta=enrollment_days_timedelta)
            
            # The list of classes from the import
            enroll_classes = row.student_import_queue.import_classes.split(',')
            class_str = ""
            if student_enabled is True:
                for enroll_class in enroll_classes:
                    # ret += " <span style='color: red; font-weight: bolder;'>Enroll " + enroll_class + "</span>"
                    if class_str != "":
                        class_str += ", "
                    class_str += enroll_class
                    Canvas.EnrollStudent(canvas_user, enroll_class)
                    Student.AddClass(row.student_import_queue.user_id, enroll_class)
                    db.commit()
            
            ret += student_display_name + " (" + student_user_name + ")"
            if row.student_import_queue.account_enabled is True:
                ret += " - <span style='color: green; font-weight: bolder;'>Imported (" + class_str + ")</span>"
            else:
                ret += " - <span style='color: red; font-weight: bolder;'>Disabled</span>"

        # Show errors
        if len(Canvas._errors) > 0:
            ret += Canvas.GetErrorString()

        if ret == "":
            ret = "Done!"
            
        return ret
