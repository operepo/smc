###### CanvasAPIClass
from gluon import *
from gluon import current

import time
import sys
import json
# from applications.smc.modules.requests import *
# from ..requests import *
# from .. import requests
# from requests import requests
import requests

# from applications.smc.modules.requests.exceptions import ConnectionError
# from ..requests.exceptions import ConnectionError
# from requests.exceptions import ConnectionError
import requests.exceptions.ConnectionError

# from .appsettings import AppSettings
from ednet.appsettings import AppSettings
# from .util import Util
from ednet.util import Util

import os
import uuid
import hashlib
from Crypto.Hash import SHA, HMAC

# Deal with change to web2py - moved AES to pyaes folder
try:
    import gluon.contrib.aes as AES
except ImportError:
    import gluon.contrib.pyaes as AES

import threading
import base64

def fast_urandom16(urandom=[], locker=threading.RLock()):
    """
    this is 4x faster than calling os.urandom(16) and prevents
    the "too many files open" issue with concurrent access to os.urandom()
    """
    try:
        return urandom.pop()
    except IndexError:
        try:
            locker.acquire()
            ur = os.urandom(16 * 1024)
            urandom += [ur[i:i + 16] for i in xrange(16, 1024 * 16, 16)]
            return ur[0:16]
        finally:
            locker.release()

def pad(s, n=32, padchar=' '):
    while ((len(s) % 32) != 0):
        s += ' '
    #pad_len = len(s) % 32 # How many characters do we need to pad out to a multiple of 32
    #if (pad_len != 0):
    #    #return s + (32 - len(s) % 32) * padchar
    #    return s + (
    return s

def AES_new(key, IV=None):
    """ Returns an AES cipher object and random IV if None specified """
    if IV is None:
        IV = fast_urandom16()

    return AES.new(key, AES.MODE_CBC, IV), IV

def encrypt(data, key):
    key = pad(key[:32])
    cipher, IV = AES_new(key)
    encrypted_data = IV + cipher.encrypt(pad(data))
    return base64.urlsafe_b64encode(encrypted_data)

def decrypt(data, key):
    key = pad(key[:32])
    if (data == None):
        data = ""
    data = base64.urlsafe_b64decode(data)
    IV, data = data[:16], data[16:]
    cipher, _ = AES_new(key, IV=IV)
    data = cipher.decrypt(data)
    data = data.rstrip(' ')
    return data


class Canvas:
    
    # Config Values
    _canvas_enabled = False
    _canvas_access_token = ""
    _canvas_server_url = ""
    _canvas_auto_create_courses = False
    
    # Errors
    _errors = []
    
    _init_run = False
    _connect_run = False
    
    _admin_user = None
    
    def __init__(self):
        pass
    
    @staticmethod
    def Init():
        if Canvas._init_run is not True:
            Canvas._canvas_enabled = AppSettings.GetValue('canvas_import_enabled', False)
            Canvas._canvas_access_token = AppSettings.GetValue('canvas_access_token', '')
            Canvas._canvas_secret = AppSettings.GetValue('canvas_secret', '')
            Canvas._canvas_server_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.correctionsed.com')
            Canvas._canvas_auto_create_courses = AppSettings.GetValue('canvas_auto_create_courses', True)
            Canvas._init_run = True
    
    @staticmethod
    def Close():
        Canvas._init_run = False
        Canvas._connect_run = False
        Canvas._errors = []
    
    @staticmethod
    def Connect():
        ret = True
        Canvas.Init()
        
        if Canvas._canvas_enabled is not True:
            return True # Canvas disabled, not an error
        
        if Canvas._canvas_server_url == "" or Canvas._canvas_access_token == "":
            Canvas._errors.append("<b>Canvas not properly configured!</b>")
            return False  # Canvas not configured
        
        if Canvas._connect_run is not True:
            # Get the admin user to see if things are working
            Canvas._admin_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self")
            if Canvas._admin_user is None or Canvas._admin_user.get('id', None) is None:
                # Invalid user
                Canvas._errors.append("<b>Canvas Error</b> - Check that your server url and DEV key is properly configured (" + str(Canvas._canvas_server_url) + ")")
                return False
            # Canvas._errors.append("Result: " + str(Canvas._admin_user))
        
        return ret

    @staticmethod
    def ConnectDB():
        try:
            canvas_db_pw = str(os.environ["IT_PW"]) + ""
        except KeyError as ex:
            # IT_PW not set?
            canvas_db_pw = "<IT_PW_NOT_SET>"
        db_canvas = None

        try:
            db_canvas = DAL('postgres://postgres:' + canvas_db_pw + '@postgresql/canvas_production', migrate=False)
        except RuntimeError as ex:
            # Error connecting, move on and return None
            db_canvas = None
        return db_canvas

    @staticmethod
    def GetCanvasSecret():
        canvas_secret = ""
        # Get the app settings value
        t = AppSettings.GetValue('canvas_secret', '<ENV>')

        # Get the environment value
        if t == "" or t == "<ENV>":
            try:
                canvas_secret = str(os.environ["CANVAS_SECRET"]).strip() + ""
            except KeyError as ex:
                # secret not set!!
                canvas_secret = ""
        else:
            canvas_secret = t

        return canvas_secret

    @staticmethod
    def EnsureDevKey():
        # Make sure that a dev key exists for OPE-Integration
        dev_key_id = 0
        msg = ""

        db_canvas = Canvas.ConnectDB()
        if db_canvas is None:
            # Unable to connect, move on
            msg += " unable to connect to canvas db"
            return 0, msg

        sql = "SELECT id FROM developer_keys WHERE name='OPE-Integration'"
        rows = db_canvas.executesql(sql)
        for row in rows:
            dev_key_id = row[0]

        # msg += " dev key is: " + str(dev_key_id)

        # If dev_key_id is 0, then we need to add a dev key to the database
        if dev_key_id == 0 or dev_key_id is None:
            dev_key = hashlib.sha224(str(uuid.uuid4()).replace('-', '').encode('utf-8')).hexdigest()
            sql = "INSERT INTO developer_keys (api_key, name) VALUES ('" + dev_key + "', 'OPE-Integration'); "
            db_canvas.executesql(sql)
            db_canvas.commit() # Make sure to commit the changes
            # msg += "  inserting new dev key..."

            # Now grab the new id
            sql = "SELECT id FROM developer_keys WHERE name='OPE-Integration'"
            rows = db_canvas.executesql(sql)
            for row in rows:
                dev_key_id = row[0]

            # msg += "  dev key is: " + str(dev_key_id)
        if dev_key_id == 0:
            # We still have a problem!
            return 0, msg

        if dev_key_id is None:
            dev_key_id = 0
        # At this point we should have a dev key setup, return its id
        return dev_key_id, msg

    @staticmethod
    def EnsureAdminAccessToken():
        # Make sure there is a dev key
        dev_key_id, msg = Canvas.EnsureDevKey()

        # Make sure we have a canvas_secret
        canvas_secret = Canvas.GetCanvasSecret()
        if canvas_secret == "":
            msg += "   No canvas secret found!"
            return "", msg

        # Connect to the canvas database
        db_canvas = Canvas.ConnectDB()

        # Find the admin user
        # sql = "SELECT id FROM users WHERE name='admin@ed'"
        sql = "SELECT user_id FROM pseudonyms WHERE unique_id='admin@ed'"
        rows = db_canvas.executesql(sql)
        user_id = 0
        for row in rows:
            user_id = row[0]

        if user_id < 1:
            msg += "  Unable to find admin user in canvas - ensure that a user exists with the admin@ed user name"
            return "", msg

        # We should have a user id and a dev key id, add an access token
        access_token = AppSettings.GetValue('canvas_access_token', "")
        if access_token == "" or access_token == "<ENV>":
            access_token = hashlib.sha224(str(uuid.uuid4()).replace('-', '').encode('utf-8')).hexdigest()
            AppSettings.SetValue('canvas_access_token', access_token)
            # msg += " Generated new access token..."

        # Make sure canvas access token matches what we have
        sql = "DELETE FROM access_tokens WHERE purpose='OPEAdminIntegration'"
        db_canvas.executesql(sql)
        hm_token = HMAC.new(canvas_secret, access_token, SHA).hexdigest()
        sql = "INSERT INTO access_tokens (developer_key_id, user_id, purpose, crypted_token, token_hint, created_at, updated_at ) VALUES ('" + str(dev_key_id) + "', '" + str(user_id) + "', 'OPEAdminIntegration', '" + str(hm_token) + "', '" + str(access_token[0:5]) + "', now(), now());"
        db_canvas.executesql(sql)
        db_canvas.commit()
        # msg += "   RAN SQL: " + sql

        return access_token, msg

    @staticmethod
    def EnsureStudentAccessToken(user_name):
        db = current.db
        # Make sure there is a dev key
        dev_key_id, msg = Canvas.EnsureDevKey()

        # Make sure we have a canvas_secret
        canvas_secret = Canvas.GetCanvasSecret()
        if canvas_secret == "":
            msg += "   No canvas secret found!"
            return "", msg

        # Connect to the canvas database
        db_canvas = Canvas.ConnectDB()

        # Find the admin user
        sql = "SELECT user_id FROM pseudonyms WHERE unique_id='" + user_name + "'"
        rows = db_canvas.executesql(sql)
        user_id = 0
        for row in rows:
            user_id = row[0]

        if user_id < 1:
            msg += "  Unable to find user in canvas: " + user_name
            return "", msg

        # We should have a user id and a dev key id, get the access token for this user
        access_token = ""
        hash = ""
        student_name = ""
        account_id = 0
        rows = db(db.auth_user.username == user_name).select(db.auth_user.id)
        for row in rows:
            # Have the auth user, lookup the student info
            account_id = row["id"]
            si_rows = db(db.student_info.account_id == account_id).select(db.student_info.canvas_auth_token, db.student_info.student_password, db.student_info.student_name)
            for si_row in si_rows:
                access_token = si_row["canvas_auth_token"]
                hash = encrypt(si_row["student_password"], access_token)
                student_name = si_row["student_name"]
        if access_token == "" or access_token == "<ENV>":
            # None present, make a new one
            access_token = hashlib.sha224(str(uuid.uuid4()).replace('-', '').encode('utf-8')).hexdigest()
            # Save access token for this user
            if account_id > 0:
                db(db.student_info.account_id == account_id).update(canvas_auth_token=access_token)
                db.commit()
            # msg += " Generated new access token..."

        # Make sure canvas access token matches what we have
        sql = "DELETE FROM access_tokens WHERE purpose='OPEStudentIntegration'"
        db_canvas.executesql(sql)
        hm_token = HMAC.new(canvas_secret, access_token, SHA).hexdigest()
        sql = "INSERT INTO access_tokens (developer_key_id, user_id, purpose, crypted_token, token_hint ) VALUES ('" + str(dev_key_id) + "', '" + str(user_id) + "', 'OPEStudentIntegration', '" + str(hm_token) + "', '" + str(access_token[0:5]) + "');"
        db_canvas.executesql(sql)
        db_canvas.commit()
        # msg += "   RAN SQL: " + sql

        return access_token, msg, hash, student_name

    
    @staticmethod
    def VerifyCanvasSettings():
        ret = False
        Canvas._errors = []
        Canvas.Close()
        con = Canvas.Connect()
        
        # Ensure that you can connect to canvas properly
        if (Canvas._canvas_enabled != True):
            Canvas._errors.append("<B>Canvas Disabled - Checks skipped</B>")
            return True
        
        if (con == True):
            Canvas._errors.append("<b>Canvas Connection Successful</b> " + Canvas._canvas_server_url + "<br />")
            Canvas._errors.append("<b>Dev Key Verified</b> <br />")
            ret = True
        
        return ret
    
    @staticmethod
    def CreateUser(user_name, password, first_name, last_name, email):
        ret = None
        
        if (Canvas.Connect() != True):
            return ret
        
        # See if the user exists
        canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/users/sis_user_id:" + user_name + "/profile")
        if 'sis_user_id' not in canvas_user:
            # Key does not exist, so no user, need to create it.
            # ret += "<b>Creating new canvas user: </b>" + user_name + "<br />"
            ### Try creating user with the API, fall back to SIS Import if needed (SIS Import handles deleted users too)
            p = dict()
            p["user[name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["user[short_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["user[sortable_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["pseudonym[unique_id]"] = user_name
            p["pseudonym[password]"] = password
            p["pseudonym[sis_user_id]"] = user_name
            p["pseudonym[send_confirmation]"] = 0
            
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/users", method="POST", params=p)
            
            # See if it worked
            canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/users/sis_user_id:" + user_name + "/profile")
            if 'sis_user_id' not in canvas_user:
                ##### Didn't work, could be deleted, do SIS import
                import_str = "user_id,login_id,password,full_name,sortable_name,short_name,email,status\n"
                parts = [ str(user_name), str(user_name), str(password), str(last_name) + ", " + str(first_name) + " (" + str(user_name) + ")", str(last_name) + ", " + str(first_name) + " (" + str(user_name) + ")", str(last_name) + ", " + str(first_name) + " (" + str(user_name) + ")", email, "active" ]

                tmp_str = "\",\"".join(parts)
                import_str += "\"" + tmp_str + "\"\n"
                # 01103,bsmith01,,Bob,Smith,Bobby Smith,bob.smith@myschool.edu,active"
                # Convert to utf-8
                import_str = unicode(import_str, "utf-8")
                # ret += "IMPORT STR: [" + import_str + "]"
                p = dict()
                p["import_type"] = "instructure_csv"
                p["batch_mode"] = 0
                p["extension"] = "csv"
                p["attachment"] = "users.csv"

                # Set header for file
                files = { 'attachment': ('users.csv', import_str, 'text/csv') }
                h = dict()
                r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/sis_imports", method="POST", params=p, files=files, headers=h)
                # ret += "IMPORT STATUS: " + str(r) + "<br />"

                # Wait a touch to let this job finish as it runs async
                tries = 0
                max_tries = 120
                time.sleep(0.5)
                if 'id' in r:
                    while tries < max_tries:
                        time.sleep(0.5)
                        progress = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/sis_imports/" + str(r["id"]))
                        # ret += "<b>Import Job:</b>" + str(tries) + " " + str(progress) + "<br/>"
                        tries += 1
                        if "progress" in progress and progress["progress"] == 100:
                            break
                    if tries >= max_tries:
                        Canvas._errors.append("<B>Error creating user! CSV Import Error - timeout waiting for import job</b> <br/>")
                        return None
                    pass

        # User exists now, update it
        p = dict()
        p["user[name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        p["user[short_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        p["user[sortable_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/users/sis_user_id:" + user_name, method="PUT", params=p)
        
        Canvas.SetPassword(user_name, password)
        
        return canvas_user

    @staticmethod
    def SetPassword(user_name, new_password):
        if (Canvas.Connect() != True):
            return False
        if (Canvas._canvas_enabled != True):
            return True
        
        # Loop through accounts and change passwords
        account_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/users/sis_user_id:" + user_name + "/logins")
        for account in account_list:
            if ("account_id" in account):
                q = dict()
                q["login[unique_id]"] = user_name
                q["login[password]"] = new_password
                q["login[sis_user_id]"] = user_name
                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(account["account_id"]) + "/logins/" + str(account["id"]), method="PUT", params=q)
                #Canvas._errors.append("Set Password for acct: [[" + str(account) + "]]")
        
        return True #True
    
    @staticmethod
    def GetCurrentClasses(user_name):
        if (Canvas.Connect() != True):
            return None
        # Get list of classes this faculty is enrolled in
        current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/users/sis_user_id:" + user_name + "/enrollments")
        #TODO check for errors
        
        return current_enrollment
    
    @staticmethod
    def CompleteAllClasses(user_name, faculty_delete=False):
        if (Canvas.Connect() != True):
            return False
        
        # Get the current list of classes
        current_enrollment = Canvas.GetCurrentClasses(user_name)
        
        for enrolled_class in current_enrollment:
            if ('type' in enrolled_class and enrolled_class['type'] == "StudentEnrollment"):
                # Students get marked as completed
                q = dict()
                q["task"] = "conclude"
                api = "/api/v1/courses/" + str(enrolled_class["course_id"]) + "/enrollments/" + str(enrolled_class["id"])
                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, api, method="DELETE", params=q)
            elif ('type' in enrolled_class and enrolled_class['type'] == "TeacherEnrollment" and faculty_delete == True):
                # Delete faculty from a class
                q = dict()
                q["task"] = "delete"
                api = "/api/v1/courses/" + str(enrolled_class["course_id"]) + "/enrollments/" + str(enrolled_class["id"])
                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, api, method="DELETE", params=q)
        return True
    
    @staticmethod
    def CreateCourse(course_name):
        if (Canvas.Connect() != True):
            return False
        
        ret = True
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses/sis_course_id:" + str(course_name))
        if ('account_id' not in course_info):
            # Course doesn't exist?!
            if (Canvas._canvas_auto_create_courses != True):
                Canvas._errors.append("<b>Course Doesn't Exist, and auto create disabled: </b>" + str(enroll_class) + "<br />")
                return True
            else:
                q = dict()
                q["account_id"] = Canvas._admin_user["id"]
                q["course[name]"] = "Auto Create - " + course_name
                q["course[course_code]"] = course_name
                q["course[sis_course_id]"] = course_name
                q["offer"] = "true"
                course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses", method="POST", params=q);

        
        return ret
    
    @staticmethod
    def EnrollStudent(canvas_user, enroll_class):
        if (Canvas.Connect() != True):
            return False
        
        enroll_class = enroll_class.strip()
        if (enroll_class == ""):
            return True
        
        if (Canvas.CreateCourse(enroll_class) != True):
            Canvas._errors.append("<B>Error enrolling student!</b> <br/>")
            return False
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses/sis_course_id:" + str(enroll_class))
        if ('account_id' not in course_info):
            # Course doesn't exist?!
            Canvas._errors.append("<b>Course Doesn't Exist, skipping enrollemnt: </b>" + str(enroll_class) + "<br />")
            return False
        
        if ('id' in canvas_user):
            # Do the enrollment
            q = dict()
            q["enrollment[user_id]"] = canvas_user["id"] # User id in the canvas system
            q["enrollment[type]"] = "StudentEnrollment"
            q["enrollment[enrollment_state]"] = "active"  # active or invite
            q["enrollment[notify]"] = "0"
            res = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/courses/" + str(course_info["id"]) + "/enrollments", method="POST", params=q)
            #log += "<b>Enrolled into couse: </b>" + str(course_info["id"]) + " " + str(enroll_class) + " - " + str(res) + "<br/>"
        else:
            # Invalid canvas user object?
            Canvas._errors.append("<b>Invalid user object when enrolling into course: </b>" + enroll_class)
            return False
        return True
    
    
    @staticmethod
    def EnrollTeacher(canvas_user, enroll_class):
        if (Canvas.Connect() != True):
            return False
        
        enroll_class = enroll_class.strip()
        if (enroll_class == ""):
            return True
        
        if (Canvas.CreateCourse(enroll_class) != True):
            Canvas._errors.append("<B>Error enrolling teacher!</b> <br/>")
            return False
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses/sis_course_id:" + str(enroll_class))
        if ('account_id' not in course_info):
            # Course doesn't exist?!
            Canvas._errors.append("<b>Course Doesn't Exist, skipping enrollemnt: </b>" + str(enroll_class) + "<br />")
            return False
        
        if ('id' in canvas_user):
            # Do the enrollment
            q = dict()
            q["enrollment[user_id]"] = canvas_user["id"] # User id in the canvas system
            q["enrollment[type]"] = "TeacherEnrollment"
            q["enrollment[enrollment_state]"] = "active"  # active or invite
            q["enrollment[notify]"] = "0"
            res = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/courses/" + str(course_info["id"]) + "/enrollments", method="POST", params=q)
            #log += "<b>Enrolled into couse: </b>" + str(course_info["id"]) + " " + str(enroll_class) + " - " + str(res) + "<br/>"
        else:
            # Invalid canvas user object?
            Canvas._errors.append("<b>Invalid user object when enrolling into course: </b>" + enroll_class)
            return False
        return True
    
    @staticmethod
    def SetQuota(user_name, quota):
        # TODO
        return True
    
    @staticmethod
    def GetErrorString():
        ret = ""
        for error in Canvas._errors:
            ret += "<div class=error_string>" + str(error) + "</div>"
        return ret
    
    @staticmethod
    def IsInClass(course_id, current_enrollment):
        ret = False

        for c in current_enrollment :
            if ('type' in c and c['type'] == "StudentEnrollment" and course_id == str(c['course_id']) ):
                ret = c['id']
        return ret

    @staticmethod
    def APICall(server, dev_key, api_call, method="GET", params=dict(), files=None, headers=dict()):
        ret = dict()
        response_items = dict()

        canvas_url = server + api_call

        headers["Authorization"] = "Bearer " + str(dev_key)

        resp = None
        try:
            if (method == "GET"):
                resp = requests.get(canvas_url, headers=headers, data=params, verify=False)
            elif (method == "POST"):
                resp = requests.post(canvas_url, headers=headers, data=params, verify=False, files=files)
            elif (method == "DELETE"):
                resp = requests.delete(canvas_url, headers=headers, data=params, verify=False)
            elif (method == "HEAD"):
                resp = requests.head(canvas_url, headers=headers, data=params, verify=False)
            elif (method == "PUT"):
                resp = requests.put(canvas_url, headers=headers, data=params, verify=False)
            elif (method == "PATCH"):
                resp = requests.patch(canvas_url, headers=headers, data=params, verify=False)
        except ConnectionError, error_message:
            Canvas._errors.append("<b>Canvas API Error:</b> " + server + "/" + api_call + " - %s" % str(error_message))
            return None
        
        if (resp != None):
            try:
                ret = resp.json()
            except ValueError, error_message:
                Canvas._errors.append("<b>JSON Error! Invalid JSON response: </b>" + str(error_message))
                return None
        return ret

    @staticmethod
    def GetQueryStringFromDictionary(params=dict()):
        ret = ""

        for key in params.keys():
            v = params[key];
            if (v != ""):
                if (ret != ""):
                    ret += "&"
                ret += key + "=" + v

        return ret


###### End CanvasAPIClass
