# -*- coding: utf-8 -*-

###### CanvasAPIClass
from gluon import *
from gluon import current

import requests
from requests.exceptions import ConnectionError
import urllib  # use for urllib.quote_plus
import urllib3 as ul3
ul3.disable_warnings()

import time
from datetime import datetime, timedelta
import sys
import json

# from .appsettings import AppSettings
from ednet.appsettings import AppSettings
# from .util import Util
from ednet.util import Util

import os
import uuid
import hashlib
from Crypto.Hash import SHA, HMAC


class Canvas:
    # When needing to do paged requests, this will get filled in after APICall
    _api_next = ""
    
    # Config Values
    _canvas_enabled = False
    _canvas_import_enabled = False
    _canvas_integration_enabled = False
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
    def isEnabled():
        Canvas.Init()
        return Canvas._canvas_enabled

    @staticmethod
    def Init():
        if Canvas._init_run is not True:
            Canvas._canvas_import_enabled = AppSettings.GetValue('canvas_import_enabled', False)
            Canvas._canvas_integration_enabled = AppSettings.GetValue('canvas_integration_enabled', False)
            Canvas._canvas_access_token = AppSettings.GetValue('canvas_access_token', '')
            Canvas._canvas_secret = AppSettings.GetValue('canvas_secret', '')
            Canvas._canvas_server_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.correctionsed.com')
            Canvas._canvas_auto_create_courses = AppSettings.GetValue('canvas_auto_create_courses', True)
            Canvas._init_run = True

            # Decide if canvas is on...
            if Canvas._canvas_integration_enabled is True or Canvas._canvas_import_enabled is True:
                Canvas._canvas_enabled = True
            else:
                Canvas._canvas_enabled = False
    
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
            return True  # Canvas disabled, not an error
        
        if Canvas._canvas_server_url == "" or Canvas._canvas_access_token == "":
            Canvas._errors.append("<b>Canvas not properly configured!</b>")
            return False  # Canvas not configured
        
        if Canvas._connect_run is not True:
            # Get the admin user to see if things are working
            Canvas._admin_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                                "/api/v1/accounts/self")
            if Canvas._admin_user is None or Canvas._admin_user.get('id', None) is None:
                # Invalid user
                Canvas._errors.append(
                    "<b>Canvas Error</b> - Check that your server url and DEV key is properly configured (" +
                    str(Canvas._canvas_server_url) + ") - " + str(Canvas._admin_user))
                return False
            # Canvas._errors.append("Result: " + str(Canvas._admin_user))
        
        return ret

    @staticmethod
    def ConnectDB():
        # Make sure to Init canvas before using _canvas?? variables
        Canvas.Init()
        
        if Canvas._canvas_enabled is not True:
            return None  # Canvas disabled, not an error

        # Grab the environ pw firs, if that isn't set, then grab the admin pw
        canvas_db_pw = AppSettings.GetValue('canvas_database_password', "<ENV>")
        # canvas.ed, postgresql will also work in docker
        pg_hostname = AppSettings.GetValue('canvas_database_server_url', 'postgresql')
        try:
            if canvas_db_pw == "" or canvas_db_pw == "<ENV>":
                canvas_db_pw = str(os.environ["IT_PW"]) + ""
        except KeyError as ex:
            # IT_PW not set?
            canvas_db_pw = "<NOT SET>"
            return None

        db_canvas = None

        # Need to strip off http stuff from hostname
        pg_hostname = pg_hostname.lower().replace("http://", "").replace("https://", "").replace("/", "")

        try:
            db_canvas = DAL('postgres://postgres:' + urllib.parse.quote_plus(canvas_db_pw)
                            + '@' + pg_hostname + '/canvas_production',
                            decode_credentials=True, migrate=False)
        except RuntimeError as ex:
            # Error connecting, move on and return None
            print("Canvas DB Error: " + str(ex))
            Canvas._errors.append(
                "<b>Canvas DB Error</b> - Unable to connect to posgresql database (" +
                str(pg_hostname) + ")")
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
        root_account_id = 0
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
            db_canvas.commit()  # Make sure to commit the changes
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

        # Make sure the workflow state is active
        sql = "UPDATE developer_keys SET workflow_state='active', visible='TRUE' WHERE name='OPE-Integration'"
        db_canvas.executesql(sql)
        db_canvas.commit()

        canvas_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.ed')
        # Strip off http and canvas
        canvas_domain = canvas_url.replace("https://canvas.", "")

        # Find the admin user - NOTE change to pull using a join and 'Site Admin' instead
        # of trying to calculate the email
        #admin_user = "admin@" + canvas_domain
        admin_user = "Site Admin"
        # sql = "SELECT id FROM users WHERE name='admin@ed'"
        #sql = "SELECT user_id, account_id FROM pseudonyms WHERE unique_id='" + admin_user + "'"
        sql = "SELECT pseudonyms.user_id, pseudonyms.account_id, accounts.root_account_id FROM pseudonyms, accounts " + \
            "WHERE pseudonyms.account_id=accounts.id and accounts.name='" + admin_user + "'"
        rows = db_canvas.executesql(sql)
        user_id = 0
        account_id = 0
        for row in rows:
            user_id = row[0]
            account_id = row[1]
            root_account_id = row[2]
        if root_account_id is None:
            # Make sure we have a good root account id
            root_account_id = 2
        
        if user_id < 1:
            msg += "  Unable to find admin user in canvas - ensure that an admin user exists with the " + admin_user + " name"
            return "", msg

        # NOTE: Need to make sure developer_key_account_bindings has a record and that it
        # is listed as "on" or we won't be able to use the key
        sql = "DELETE FROM developer_key_account_bindings WHERE account_id=" + str(account_id) + \
              " and developer_key_id=" + str(dev_key_id)
        db_canvas.executesql(sql)
        sql = "INSERT INTO developer_key_account_bindings (account_id, developer_key_id, " + \
              "workflow_state, created_at, updated_at, root_account_id) VALUES (" + str(account_id) + \
              ", " + str(dev_key_id) + ", 'on', now(), now(), " + str(root_account_id) + ")"
        db_canvas.executesql(sql)

        # At this point we should have a dev key setup, return its id
        return dev_key_id, msg, root_account_id

    @staticmethod
    def FlushRedisKeys(pattern):
        # TODO - TODO - pull only patterns?
        # Try and connect to canvas redis server and flush the
        # redis keys that match the pattern
        canvas_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.ed')
        # Strip off http and canvas
        canvas_domain = canvas_url.replace("https://canvas.", "")
        redis_url = "redis." + canvas_domain
        # NOTE - Should be linked in docker to hostname redis
        redis_url = "redis"
        had_error = False
        import redis

        try:
            r = redis.Redis(host=redis_url, port=6379, socket_connect_timeout=5)  # password=...
            r.flushdb()
        except Exception as ex:
            print("Error flushing redis db: " + str(ex))
            had_error = True

        if had_error is True:
            # Try again w different redis url
            redis_url = 'redis'
            try:
                r = redis.Redis(host=redis_url, port=6379)  # password=...
                r.flushdb()
            except Exception as ex:
                print("Error flushing redis db: " + str(ex))
                had_error = True


    @staticmethod
    def EnsureAdminAccessToken():
        # Connect to the canvas database
        db_canvas = Canvas.ConnectDB()
        if db_canvas is None:
            return "", "Error - Can't connect to Canvas Postgresql Database!"

        # Make sure there is a dev key
        dev_key_id, msg, root_account_id = Canvas.EnsureDevKey()
        if dev_key_id == 0:
            return "", "Error setting up dev key! " + msg

        canvas_url = AppSettings.GetValue('canvas_server_url', 'https://canvas.ed')
        # Strip off http and canvas
        canvas_domain = canvas_url.replace("https://canvas.", "")

        # Make sure we have a canvas_secret
        canvas_secret = Canvas.GetCanvasSecret()
        if canvas_secret == "":
            msg += "   No canvas secret found!"
            return "", msg

        # Find the admin user
        admin_user = "admin@" + canvas_domain
        # sql = "SELECT id FROM users WHERE name='admin@ed'"
        sql = "SELECT user_id, account_id FROM pseudonyms WHERE unique_id='" + admin_user + "'"
        rows = db_canvas.executesql(sql)
        user_id = 0
        account_id = 0
        for row in rows:
            user_id = row[0]
            account_id = row[1]

        if user_id < 1:
            msg += "  Unable to find admin user in canvas - ensure that a user exists with the " + admin_user + " user name"
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
        hm_token = HMAC.new(canvas_secret.encode('utf-8'), access_token.encode('utf-8'), digestmod=SHA).hexdigest()
        sql = "INSERT INTO access_tokens (developer_key_id, user_id, purpose, crypted_token, token_hint," + \
              " created_at, updated_at ) VALUES ('" + str(dev_key_id) + "', '" + str(user_id) + \
              "', 'OPEAdminIntegration', '" + str(hm_token) + "', '" + str(access_token[0:5]) + "', now(), now());"
        db_canvas.executesql(sql)
        db_canvas.commit()
        # msg += "   RAN SQL: " + sql

        # Make sure redis info is flushed
        Canvas.FlushRedisKeys("*keys*")

        return access_token, msg

    @staticmethod
    def EnsureStudentAccessToken(user_name):
        db = current.db
        # Make sure there is a dev key
        dev_key_id, msg, root_account_id = Canvas.EnsureDevKey()
        if dev_key_id == 0:
            return "", "Error setting dev key, make sure SMC is linked to canvas (Admin -> Canvas Settings/Verify) - " + msg, "", ""

        # Make sure we have a canvas_secret
        canvas_secret = Canvas.GetCanvasSecret()
        if canvas_secret == "":
            msg += "   No canvas secret found!"
            return "", msg, "", ""

        # Connect to the canvas database
        db_canvas = Canvas.ConnectDB()

        if db_canvas is None:
            msg += " - Canvas DB Connection is None"
            return "", msg, "", ""

        # Find the admin user
        sql = "SELECT user_id, account_id FROM pseudonyms WHERE unique_id='" + user_name + "'"
        rows = db_canvas.executesql(sql)
        user_id = 0
        account_id = 0
        for row in rows:
            user_id = row[0]
            account_id = row[1]

        if user_id < 1:
            msg += "  Unable to find user in canvas: " + user_name
            return "", msg, "", ""

        # We should have a user id and a dev key id, get the access token for this user
        access_token = ""
        hash = ""
        student_name = ""
        student_pw = ""
        uid = ""
        account_id = 0
        rows = db(db.auth_user.username == user_name).select(db.auth_user.id)
        for row in rows:
            # Have the auth user, lookup the student info
            account_id = row["id"]
            si_rows = db(db.student_info.account_id == account_id).select(db.student_info.canvas_auth_token,
                                                                          db.student_info.student_password,
                                                                          db.student_info.student_name,
                                                                          db.student_info.user_id)
            for si_row in si_rows:
                access_token = si_row["canvas_auth_token"]
                student_pw = si_row["student_password"]
                student_name = si_row["student_name"]
                uid = si_row["user_id"]
                
                # Deal w password if it is scrambled (bug in encryption left some passwords scrambled)
            try:
                # If pw ok, this works and we just move on
                unicode_pw = ('\"' + student_pw + '\"').encode('utf-16-le', 'replace')
            except:
                # If scrambled pw, encoding w unicode will throw an error, setup the default pw.
                new_pw = AppSettings.GetValue('student_password_pattern', 'Sid<user_id>!')
                student_pw = new_pw.replace('<user_id>', uid)
        if access_token == "" or access_token == "<ENV>":
            # None present, make a new one
            access_token = hashlib.sha224(str(uuid.uuid4()).replace('-', '').encode('utf-8')).hexdigest()
            # Save access token for this user
            if account_id > 0:
                db(db.student_info.account_id == account_id).update(canvas_auth_token=access_token)
                db.commit()
            # msg += " Generated new access token..."

        # Make sure canvas access token matches what we have
        sql = "DELETE FROM access_tokens WHERE purpose='OPEStudentIntegration' and user_id='" + str(user_id) + "'"
        db_canvas.executesql(sql)
        hm_token = HMAC.new(canvas_secret.encode('utf-8'), access_token.encode('utf-8'), digestmod=SHA).hexdigest()
        sql = "INSERT INTO access_tokens (developer_key_id, user_id, purpose, crypted_token, token_hint," + \
              " created_at, updated_at, root_account_id ) VALUES ('" + str(dev_key_id) + "', '" + str(user_id) + \
              "', 'OPEStudentIntegration', '" + str(hm_token) + "', '" + str(access_token[0:5]) + "', now(), now(), " + str(root_account_id) + " );"
        db_canvas.executesql(sql)
        db_canvas.commit()
        # msg += "   RAN SQL: " + sql
        
        # Calculate pw hash
        hash = Util.encrypt(student_pw, access_token)

        # Make sure redis info is flushed
        # Start a background process so we can return right away
        scheduler = current.scheduler
        result = scheduler.queue_task('flush_redis_keys', timeout=60,
                                      immediate=True, sync_output=5, group_name="misc")
        
        #Canvas.FlushRedisKeys("*keys*")

        return access_token, msg, hash, student_name

    @staticmethod
    def VerifyCanvasSettings():
        ret = False
        Canvas._errors = []
        Canvas.Close()
        con = Canvas.Connect()

        had_errors = False
        
        # Ensure that you can connect to canvas properly
        if Canvas._canvas_enabled is not True:
            Canvas._errors.append("<B>Canvas Account Import Disabled - API checks skipped</B>")
            return True
        
        if con is True:
            Canvas._errors.append("<b>Canvas Integration Connection Successful</b> " + Canvas._canvas_server_url +
                                  "<br />")
            Canvas._errors.append("<b>Dev Key Verified</b> <br />")
        else:
            had_errors = True

        db = Canvas.ConnectDB()
        if db is not None:
            Canvas._errors.append(
                "<b>Canvas DB Connection Successful</b><br />")
        else:
            Canvas._errors.append(
                "<b>Canvas DB Connection Failed</b><br />")
            had_errors = True

        if had_errors == True:
            ret = False
        else:
            ret = True
            
        return ret
    
    @staticmethod
    def CreateUser(user_name, password, first_name, last_name, email):
        ret = None
        
        if Canvas.Connect() is not True:
            return ret
        
        # See if the user exists
        canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/users/sis_user_id:" + user_name + "/profile")
        if 'sis_user_id' not in canvas_user:
            # Key does not exist, so no user, need to create it.
            # ret += "<b>Creating new canvas user: </b>" + user_name + "<br />"
            # Try creating user with the API, fall back to SIS Import if needed (SIS Import handles deleted users too)
            p = dict()
            # old py2 - needed unicode
            #p["user[name]"] = str.encode(last_name + ", " + first_name + " (" + user_name + ")").encode('utf-8')
            #p["user[short_name]"] = str.encode(last_name + ", " + first_name + " (" + user_name + ")").encode('utf-8')
            #p["user[sortable_name]"] = str.encode(last_name + ", " + first_name + " (" +
            #                                      user_name + ")").encode('utf-8')
            #p["pseudonym[unique_id]"] = str.encode(user_name).encode('utf-8')
            #p["pseudonym[password]"] = str.encode(password).encode('utf-8')
            #p["pseudonym[sis_user_id]"] = str.encode(user_name).encode('utf-8')
            #p["pseudonym[send_confirmation]"] = 0

            # py3 - already unicode
            p["user[name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["user[short_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["user[sortable_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
            p["pseudonym[unique_id]"] = user_name
            p["pseudonym[password]"] = password
            p["pseudonym[sis_user_id]"] = user_name
            p["pseudonym[send_confirmation]"] = 0
            
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/users",
                               method="POST", params=p)
            
            # See if it worked
            canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                         "/api/v1/users/sis_user_id:" + user_name + "/profile")
            if 'sis_user_id' not in canvas_user:
                # Didn't work, could be deleted, do SIS import
                import_str = "user_id,login_id,password,full_name,sortable_name,short_name,email,status\n"
                parts = [str(user_name), str(user_name), str(password), str(last_name) + ", " + str(first_name) +
                         " (" + str(user_name) + ")", str(last_name) + ", " + str(first_name) + " (" +
                         str(user_name) + ")", str(last_name) + ", " + str(first_name) + " (" + str(user_name) + ")",
                         email, "active"]

                tmp_str = "\",\"".join(parts)
                import_str += "\"" + tmp_str + "\"\n"
                # 01103,bsmith01,,Bob,Smith,Bobby Smith,bob.smith@myschool.edu,active"
                # Convert to utf-8
                # Note - not needed - running on py3, already unicode
                #import_str = unicode(import_str, "utf-8")


                # ret += "IMPORT STR: [" + import_str + "]"
                p = dict()
                p["import_type"] = "instructure_csv"
                p["batch_mode"] = 0
                p["extension"] = "csv"
                p["attachment"] = "users.csv"

                # Set header for file
                files = {'attachment': ('users.csv', import_str, 'text/csv')}
                h = dict()
                r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/sis_imports",
                                   method="POST", params=p, files=files, headers=h)
                # ret += "IMPORT STATUS: " + str(r) + "<br />"

                # Wait a touch to let this job finish as it runs async
                tries = 0
                max_tries = 120
                time.sleep(0.5)
                if 'id' in r:
                    while tries < max_tries:
                        time.sleep(0.5)
                        progress = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                                  "/api/v1/accounts/" + str(Canvas._admin_user["id"]) +
                                                  "/sis_imports/" + str(r["id"]))
                        # ret += "<b>Import Job:</b>" + str(tries) + " " + str(progress) + "<br/>"
                        tries += 1
                        if "progress" in progress and progress["progress"] == 100:
                            break
                    if tries >= max_tries:
                        Canvas._errors.append(
                            "<B>Error creating user! CSV Import Error - timeout waiting for import job</b> <br/>")
                        return None
                    pass

        # User exists now, update it
        p = dict()
        p["user[name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        p["user[short_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        p["user[sortable_name]"] = last_name + ", " + first_name + " (" + user_name + ")"
        canvas_user = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/users/sis_user_id:" + user_name, method="PUT", params=p)
        
        Canvas.SetPassword(user_name, password)
        
        return canvas_user

    @staticmethod
    def SetPassword(user_name, new_password):
        if Canvas.Connect() is not True:
            return False
        if Canvas._canvas_enabled is not True:
            return True
        
        # Loop through accounts and change passwords
        account_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                      "/api/v1/users/sis_user_id:" + user_name + "/logins")
        for account in account_list:
            if "account_id" in account:
                q = dict()
                q["login[unique_id]"] = user_name
                q["login[password]"] = new_password
                q["login[sis_user_id]"] = user_name
                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                               "/api/v1/accounts/" + str(account["account_id"]) + "/logins/" + str(account["id"]),
                               method="PUT", params=q)
                # Canvas._errors.append("Set Password for acct: [[" + str(account) + "]]")
        
        return True  # True
    
    @staticmethod
    def GetCurrentClasses(user_name):
        if Canvas.Connect() is not True:
            return None
        # Get list of classes this faculty is enrolled in
        current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                            "/api/v1/users/sis_user_id:" + user_name + "/enrollments")
        # TODO check for errors
        
        return current_enrollment
    
    @staticmethod
    def CompleteAllClasses(user_name, faculty_delete=False, enrollment_days_timedelta=None):
        if Canvas.Connect() is not True:
            return False

        if enrollment_days_timedelta is None:
            # Drop students if the enrollment update date is over this amount
            enrollment_days_timedelta = timedelta(days=100)
        
        # Get the current list of classes
        current_enrollment = Canvas.GetCurrentClasses(user_name)
        
        for enrolled_class in current_enrollment:
            if 'type' in enrolled_class and enrolled_class['type'] == "StudentEnrollment":
                # See if it is time to mark student as completed
                complete_before = datetime.now() - enrollment_days_timedelta
                # 2018-11-22T06:35:51Z
                e_time = datetime.strptime(enrolled_class['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                if e_time < complete_before:
                    # Students get marked as completed
                    # print("Marking class as completed " + str(enrolled_class['course_id']))
                    q = dict()
                    q["task"] = "conclude"
                    api = "/api/v1/courses/" + str(enrolled_class["course_id"]) + "/enrollments/" + \
                          str(enrolled_class["id"])
                    Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, method="DELETE", params=q)
                else:
                    # print("Class is too new, not completing " + str(enrolled_class['course_id']) +
                    #       "  " + str(e_time) + " / " + str(complete_before))
                    continue
            elif 'type' in enrolled_class and enrolled_class['type'] == "TeacherEnrollment" and faculty_delete is True:
                # Delete faculty from a class
                q = dict()
                q["task"] = "delete"
                api = "/api/v1/courses/" + str(enrolled_class["course_id"]) + "/enrollments/" + \
                      str(enrolled_class["id"])
                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, api, method="DELETE", params=q)
        return True
    
    @staticmethod
    def CreateCourse(course_name):
        if Canvas.Connect() is not True:
            return False
        
        ret = True
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses/sis_course_id:" +
                                     str(course_name))
        if 'account_id' not in course_info:
            # Course doesn't exist?!
            if Canvas._canvas_auto_create_courses is not True:
                Canvas._errors.append("<b>Course Doesn't Exist, and auto create disabled: </b>" +
                                      str(course_name) + "<br />")
                return True
            else:
                q = dict()
                q["account_id"] = Canvas._admin_user["id"]
                q["course[name]"] = "Auto Create - " + course_name
                q["course[course_code]"] = course_name
                q["course[sis_course_id]"] = course_name
                q["offer"] = "true"
                course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                             "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses",
                                             method="POST", params=q)
        
        return ret
    
    @staticmethod
    def EnrollStudent(canvas_user, enroll_class):
        if Canvas.Connect() is not True:
            return False
        
        enroll_class = enroll_class.strip()
        if enroll_class == "":
            return True
        
        if Canvas.CreateCourse(enroll_class) is not True:
            Canvas._errors.append("<B>Error enrolling student!</b> <br/>")
            return False
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/accounts/" + str(Canvas._admin_user["id"]) +
                                     "/courses/sis_course_id:" + str(enroll_class))
        if 'account_id' not in course_info:
            # Course doesn't exist?!
            Canvas._errors.append("<b>Course Doesn't Exist, skipping enrollment: </b>" + str(enroll_class) + "<br />")
            return False
        
        if 'id' in canvas_user:
            # Do the enrollment
            q = dict()
            q["enrollment[user_id]"] = canvas_user["id"]  # User id in the canvas system
            q["enrollment[type]"] = "StudentEnrollment"
            q["enrollment[enrollment_state]"] = "active"  # active or invite
            q["enrollment[notify]"] = "0"
            res = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/courses/" +
                                 str(course_info["id"]) + "/enrollments", method="POST", params=q)
            # log += "<b>Enrolled into course: </b>" + str(course_info["id"]) +
            # " " + str(enroll_class) + " - " + str(res) + "<br/>"
        else:
            # Invalid canvas user object?
            Canvas._errors.append("<b>Invalid user object when enrolling into course: </b>" + enroll_class)
            return False
        return True

    @staticmethod
    def EnrollTeacher(canvas_user, enroll_class):
        if Canvas.Connect() is not True:
            return False
        
        enroll_class = enroll_class.strip()
        if enroll_class == "":
            return True
        
        if Canvas.CreateCourse(enroll_class) is not True:
            Canvas._errors.append("<B>Error enrolling teacher!</b> <br/>")
            return False
        
        # Get the course info
        course_info = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/accounts/" + str(Canvas._admin_user["id"]) + "/courses/sis_course_id:" +
                                     str(enroll_class))
        if 'account_id' not in course_info:
            # Course doesn't exist?!
            Canvas._errors.append("<b>Course Doesn't Exist, skipping enrollment: </b>" + str(enroll_class) + "<br />")
            return False
        
        if 'id' in canvas_user:
            # Do the enrollment
            q = dict()
            q["enrollment[user_id]"] = canvas_user["id"] # User id in the canvas system
            q["enrollment[type]"] = "TeacherEnrollment"
            q["enrollment[enrollment_state]"] = "active"  # active or invite
            q["enrollment[notify]"] = "0"
            res = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                 "/api/v1/courses/" + str(course_info["id"]) + "/enrollments", method="POST", params=q)
            # log += "<b>Enrolled into couse: </b>" + str(course_info["id"]) +
            # " " + str(enroll_class) + " - " + str(res) + "<br/>"
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
            if 'type' in c and c['type'] == "StudentEnrollment" and course_id == str(c['course_id']):
                ret = c['id']
        return ret

    @staticmethod
    def APICall(server, dev_key, api_call, method="GET", params=None, files=None, headers=None):
        ret = dict()
        if params is None:
            params = dict()
        if headers is None:
            headers = dict()
        response_items = dict()

        # Reset the next link - for paging
        Canvas._api_next = ""
        canvas_url = server + api_call

        headers["Authorization"] = "Bearer " + str(dev_key)

        resp = None
        try:
            if method == "GET":
                resp = requests.get(canvas_url, headers=headers, data=params, verify=False)
            elif method == "POST":
                resp = requests.post(canvas_url, headers=headers, data=params, verify=False, files=files)
            elif method == "DELETE":
                resp = requests.delete(canvas_url, headers=headers, data=params, verify=False)
            elif method == "HEAD":
                resp = requests.head(canvas_url, headers=headers, data=params, verify=False)
            elif method == "PUT":
                resp = requests.put(canvas_url, headers=headers, data=params, verify=False)
            elif method == "PATCH":
                resp = requests.patch(canvas_url, headers=headers, data=params, verify=False)
        except ConnectionError as error_message:
            Canvas._errors.append("<b>Canvas API Error:</b> " + server + "/" + api_call + " - %s" % str(error_message))
            return None
        
        if resp is not None:
            # Pull the next link out of the header
            link = resp.headers.get("Link")
            if link is not None:
                # print("Next Page: " + link)
                # Split the links
                links = link.split(',')
                for l in links:
                    if 'rel="next"' in l:
                        # print("Found Next: " + l)
                        # Found the link
                        p = l.split(";")
                        # Save the link w out the <> around it
                        next_link = p[0].replace("<", "").replace(">", "")
                        # Save the next_link so we can use it later to grab the next page
                        Canvas._api_next = next_link
                        # print(" Got Next: " + Canvas._api_next)

            try:
                ret = resp.json()
            except ValueError as error_message:
                Canvas._errors.append("<b>JSON Error! Invalid JSON response: </b>" + str(error_message))
                return None
        return ret

    @staticmethod
    def GetQueryStringFromDictionary(params=None):
        ret = ""
        if params is None:
            params = dict()

        for key in params.keys():
            v = params[key];
            if v != "":
                if ret != "":
                    ret += "&"
                ret += key + "=" + v

        return ret

    @staticmethod
    def get_sections_for_course(course_id):
        Canvas.Init()
        api = f"/api/v1/courses/{course_id}/sections"

        p = dict()
        p["per_page"] = 200000

        sections_list = dict()

        current_sections = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
            api, params=p)
        
        if current_sections is None:
            print(f"Error pulling canvas sections for course: {api}")
            return sections_list
         
        # Save next_url in case there are more pages to get
        next_url = Canvas._api_next

        for c in current_sections:
            if 'id' in c and 'name' in c:
                sections_list[c['id']] = c['name']
            else:
                sections_list["ERROR"] = f"ERR ({course_id}) - Unable to find sections."

        # Keep grabbing more until we run out of pages
        while next_url != '':
            # Strip off server name
            api = next_url.replace(Canvas._canvas_server_url, "")
            current_sections = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                                api)  # don't send params, params=p)
            if current_sections is None:
                print(f"Error pulling canvas course sections - {api}")
                return sections_list

            next_url = Canvas._api_next

            for c in current_sections:
                if 'id' in c and 'name' in c:
                    sections_list[c['id']] = c['name']
                else:
                    sections_list["ERROR"] = f"ERR ({course_id}) - Unable to find sections."

        return sections_list


    @staticmethod
    def get_courses_for_student(student):
        Canvas.Init()
        api = "/api/v1/users/sis_login_id:" + student + "/courses"
        
        p = dict()
        p["per_page"] = 200000

        course_list = dict()

        current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                            api, params=p)

        if current_enrollment is None:
            print("Error pulling canvas enrollment - " + str(api))
            return course_list

        # Save next_url in case there are more pages to get
        next_url = Canvas._api_next

        for c in current_enrollment:
            if 'id' in c and 'name' in c:
                course_list[c['id']] = c['name']
            else:
                course_list["ERROR"] = "ERR (" + str(student) + ") - Is this user in canvas? SIS_LOGIN_ID doesn't match."

        # Keep grabbing more until we run out of pages
        while next_url != '':
            # Strip off server name
            api = next_url.replace(Canvas._canvas_server_url, "")
            current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                                api)  # don't send params, params=p)
            if current_enrollment is None:
                print("Error pulling canvas enrollment - " + str(api))
                return course_list

            next_url = Canvas._api_next

            for c in current_enrollment:
                if 'id' in c and 'name' in c:
                    course_list[c['id']] = c['name']
                else:
                    course_list["ERROR"] = "ERR (" + str(student) + ") - Is this user in canvas? SIS_LOGIN_ID doesn't match."

        return course_list

    @staticmethod
    def get_courses_for_faculty(faculty):
        Canvas.Init()
        # if faculty is 'admin', then get all courses
        #api = "/api/v1/users/sis_user_id:" + faculty + "/courses"
        api = "/api/v1/users/sis_login_id:" + faculty + "/courses"
        if faculty == 'admin':
            api = "/api/v1/accounts/1/courses"

        p = dict()
        p["per_page"] = 200000

        course_list = dict()

        current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                            api, params=p)

        if current_enrollment is None:
            print("Error pulling canvas enrollment - " + str(api))
            return course_list

        # Save next_url in case there are more pages to get
        next_url = Canvas._api_next

        for c in current_enrollment:
            if 'id' in c and 'name' in c:
                course_list[c['id']] = c['name']
            else:
                course_list["ERROR"] = "ERR (" + str(faculty) + ") - Is this user in canvas? SIS_LOGIN_ID doesn't match."

        # Keep grabbing more until we run out of pages
        while next_url != '':
            # Strip off server name
            api = next_url.replace(Canvas._canvas_server_url, "")
            current_enrollment = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                                api)  # don't send params, params=p)
            if current_enrollment is None:
                print("Error pulling canvas enrollment - " + str(api))
                return course_list

            next_url = Canvas._api_next

            for c in current_enrollment:
                if 'id' in c and 'name' in c:
                    course_list[c['id']] = c['name']
                else:
                    course_list["ERROR"] = "ERR (" + str(faculty) + ") - Is this user in canvas? SIS_LOGIN_ID doesn't match."

        return course_list

    @staticmethod
    def get_id_for_filename(course_id, file_name):
        ret = "<FILE_ID_NOT_FOUND_" + file_name + ">"
        Canvas.Init()

        api = "/api/v1/courses/" + course_id + "/files/?search_term=" + str(file_name)

        p = dict()
        p["per_page"] = 20000

        files_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, params=p)

        if files_list is None:
            print("File not found - " + str(api))
            return ret

        # Should be a list of files (should be 1)
        for f in files_list:
            # Need to make an API call to get the page body
            ret = f['id']
            break  # just grab the first match

        return ret

    @staticmethod
    def get_assignment_list_for_course(course_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/assignments"

        p = dict()
        p["per_page"] = 50

        next_url = ""

        item_bodies = dict()

        item_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, params=p)
        if item_list is None:
            print("Error pulling assignment list - " + str(api))
            return item_bodies

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)

        for i in item_list:
            # Store the item in the list
            item_bodies[i['id']] = i["description"]

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            item_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                       api)  # Note - don't send params, they are in the api url
            if item_list is None:
                print("Error pulling assignment list - " + str(api))
                return item_bodies

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for i in item_list:
                # print("P: " + str(p))

                item_bodies[i['id']] = i["description"]

        return item_bodies

    @staticmethod
    def get_discussion_list_for_course(course_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/discussion_topics"

        p = dict()
        p["per_page"] = 50

        next_url = ""

        item_bodies = dict()

        item_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                    api, params=p)
        if item_list is None:
            print("Error pulling discussion topics - " + str(api))
            return item_bodies

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)

        for i in item_list:
            # Store the item in the list
            item_bodies[i['id']] = i["message"]

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            item_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                        api)  # Note - don't send params, they are in the api url
            if item_list is None:
                print("Error pulling discussion topics - " + str(api))
                return item_bodies

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for i in item_list:
                # print("P: " + str(p))

                item_bodies[i['id']] = i["message"]

        return item_bodies

    @staticmethod
    def get_quiz_list_for_course(course_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes"

        p = dict()
        p["per_page"] = 50

        next_url = ""

        quiz_bodies = dict()

        quiz_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, params=p)
        if quiz_list is None:
            print("Error pulling quiz list - " + str(api))
            return quiz_bodies

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)

        for q in quiz_list:
            # Need to make an API call to get the page body
            quiz_bodies[q['id']] = q["description"]

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            quiz_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                       api)  # Note - don't send params, they are in the api url
            if quiz_list is None:
                print("Error pulling quiz list - " + str(api))
                return quiz_bodies

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for q in quiz_list:
                # print("P: " + str(p))

                quiz_bodies[q['id']] = q["description"]

        return quiz_bodies

    @staticmethod
    def get_question_payload_for_quiz(course_id, quiz_id, user_auth_key):
        payload = list()

        # Get the list of questions for this quiz
        Canvas.Init()
        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id) + "/questions"

        p = dict()
        p["per_page"] = 50

        next_url = ""
        question_objects = dict()

        question_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                    api, params=p)
        if question_list is None:
            print("Error pulling question list - " + str(api))
            return payload

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)

        for q in question_list:
            question_objects[q['id']] = q

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            question_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                       api)  # Note - don't send params, they are in the api url
            if question_list is None:
                print("Error pulling question list - " + str(api))
                break

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for q in question_list:
                # print("P: " + str(p))
                question_objects[q['id']] = q

        # We have the questions, process them and put them in the payload
        for qid in question_objects:
            # payload question
            q = question_objects[qid]
            question_id = q["id"]
            quizz_id = q['quiz_id']
            pq = dict()
            pq["id"] = question_id
            pq["course_id"] = course_id
            pq["quiz_id"] = q["quiz_id"]
            pq["position"] = q["position"]
            pq["question_type"] = q["question_type"]
            pq["quiz_group_id"] = q["quiz_group_id"]

            payload_token = str(uuid.uuid4()).replace("-","")
            pq["payload_token"] = payload_token

            json_str = json.dumps(q)
            # Build the payload_hash
            h = hashlib.sha256()
            h.update(user_auth_key.encode())
            h.update(str(course_id).encode())
            h.update(str(quiz_id).encode())
            h.update(str(question_id).encode())
            h.update(payload_token.encode())

            enc_key = h.hexdigest()
            
            # Encrypt the payload
            pl = Util.encrypt(json_str, enc_key)
            pq["question_payload"] = pl.decode()
            payload.append(pq)

        return payload


    @staticmethod
    def get_quiz_questions_for_quiz(course_id, quiz_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id) + "/questions"

        p = dict()
        p["per_page"] = 50

        next_url = ""
        question_bodies = dict()

        question_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                    api, params=p)
        if question_list is None:
            print("Error pulling question list - " + str(api))
            return question_bodies

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)

        for q in question_list:
            # Need to make an API call to get the page body
            question_bodies[q['id']] = q["question_text"]

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            question_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                       api)  # Note - don't send params, they are in the api url
            if question_list is None:
                print("Error pulling question list - " + str(api))
                return question_bodies

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for q in question_list:
                # print("P: " + str(p))
                question_bodies[q['id']] = q["question_text"]

        return question_bodies

    @staticmethod
    def update_discussion_for_course(course_id, discussion_id, params):
        # Post page to course
        res = False

        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/discussion_topics/" + str(discussion_id)

        p = dict()
        # p["per_page"] = 20000
        p = params

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p, method="PUT")

        res = str(page)

        return res

    @staticmethod
    def update_assignment_for_course(course_id, assignment_id, params):
        # Post page to course
        res = False

        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/assignments/" + str(assignment_id)

        p = dict()
        # p["per_page"] = 20000
        p = params

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p, method="PUT")

        res = str(page)

        return res

    @staticmethod
    def update_quiz_for_course(course_id, quiz_id, params):
        # Post page to course
        res = False

        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id)

        p = dict()
        # p["per_page"] = 20000
        p = params

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p, method="PUT")

        res = str(page)

        return res

    @staticmethod
    def update_quiz_question_for_course(course_id, quiz_id, qq_id, params):
        # Post page to course
        res = False

        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id) + "/questions/" + str(qq_id)

        p = dict()
        # p["per_page"] = 20000
        p = params

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p, method="PUT")

        res = str(page)

        return res

    @staticmethod
    def get_page_list_for_course(course_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/pages"

        p = dict()
        p["per_page"] = 50

        next_url = ""
        page_bodies = dict()

        page_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, params=p)
        if page_list is None:
            print("Error pulling page list - " + str(api))
            return page_bodies

        # If there are more pages, _api_next should have the link to the next page
        next_url = Canvas._api_next
        # print("Next URL: " + next_url)
        # Should be a list of pages, now get individual page bodies

        for p in page_list:
            # Need to make an API call to get the page body
            page = Canvas.get_page_for_course(course_id, p['url'])
            if page is not None:
                page_bodies[p['url']] = page["body"]

        while next_url != '':
            # Calls to get more results (and strip off https://canvas.ed/)
            api = next_url.replace(Canvas._canvas_server_url, "")
            # print("Next API: " + api)
            page_list = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                api)  # Note - don't send params, they are in the api url
            if page_list is None:
                print("Error pulling page list - " + str(api))
                return page_bodies

            # If there are more pages, _api_next should have the link to the next page
            next_url = Canvas._api_next
            # print("Next URL: " + next_url)

            for p in page_list:
                # print("P: " + str(p))
                page = Canvas.get_page_for_course(course_id, p['url'])
                if page is not None:
                    page_bodies[p['url']] = page["body"]

        return page_bodies

    @staticmethod
    def get_page_for_course(course_id, page_url):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/pages/" + page_url

        p = dict()
        p["per_page"] = 20000

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                   api, params=p)

        return page

    @staticmethod
    def get_quiz_for_course(course_id, quiz_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id)

        p = dict()
        p["per_page"] = 20000

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p)

        return page

    @staticmethod
    def get_question_for_course(course_id, quiz_id, question_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/quizzes/" + str(quiz_id) + "/questions/" + str(question_id)

        p = dict()
        p["per_page"] = 20000

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p)

        return page

    @staticmethod
    def get_discussion_for_course(course_id, discussion_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/discussion_topics/" + str(discussion_id)

        p = dict()
        p["per_page"] = 20000

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p)

        return page

    @staticmethod
    def get_assignment_for_course(course_id, assignment_id):
        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/assignments/" + str(assignment_id)

        p = dict()
        p["per_page"] = 20000

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p)

        return page

    @staticmethod
    def update_page_for_course(course_id, page_url, page):
        # Post page to course
        res = False

        Canvas.Init()

        api = "/api/v1/courses/" + str(course_id) + "/pages/" + page_url

        p = dict()
        # p["per_page"] = 20000
        p = page

        page = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                              api, params=p, method="PUT")

        res = str(page)

        return res

    @staticmethod
    def replace_value_in_course_page(course_id, page_url, find_value, replace_value):
        # First - get the original page info
        page = Canvas.get_page_for_course(course_id, page_url)
        if page is None:
            print("Unable to find page (replace_value_in_course_page): " + str(page_url))
            return
        new_page = dict()
        new_page["wiki_page[body]"] = page["body"].replace(find_value, replace_value)

        # Now submit page back to canvas
        Canvas.update_page_for_course(course_id, page_url, new_page)

        pass

    @staticmethod
    def replace_value_in_quiz_page(course_id, quiz_id, find_value, replace_value):
        # First - get the original page info
        quiz = Canvas.get_quiz_for_course(course_id, quiz_id)
        if quiz is None:
            print("Unable to find quiz (replace_value_in_quiz_page): " + str(quiz_id))
            return
        new_page = dict()
        new_page["quiz[description]"] = quiz["description"].replace(find_value, replace_value)

        # Now submit page back to canvas
        Canvas.update_quiz_for_course(course_id, quiz_id, new_page)

        pass

    @staticmethod
    def replace_value_in_question_page(course_id, quiz_id, question_id, find_value, replace_value):
        # First - get the original page info
        question = Canvas.get_question_for_course(course_id, quiz_id, question_id)
        if question is None:
            print("Unable to find question (replace_value_in_question_page): " + str(quiz_id) + "/" + str(question_id))
            return
        new_page = dict()
        new_page["question[question_text]"] = question["question_text"].replace(find_value, replace_value)

        # Now submit page back to canvas
        Canvas.update_quiz_question_for_course(course_id, quiz_id, question_id, new_page)

        pass

    @staticmethod
    def replace_value_in_discussion_page(course_id, discussion_id, find_value, replace_value):
        # First - get the original page info
        discussion = Canvas.get_discussion_for_course(course_id, discussion_id)
        if discussion is None:
            print("Unable to find discussion (replace_value_in_discussion_page): " + str(discussion_id))
            return
        new_page = dict()
        new_page["message"] = discussion["message"].replace(find_value, replace_value)

        # Now submit page back to canvas
        Canvas.update_discussion_for_course(course_id, discussion_id, new_page)

        pass

    @staticmethod
    def replace_value_in_assignment_page(course_id, assignment_id, find_value, replace_value):
        # First - get the original page info
        assignment = Canvas.get_assignment_for_course(course_id, assignment_id)
        if assignment is None:
            print("Unable to find assignment (replace_value_in_assignment_page): " + str(assignment_id))
            return
        new_page = dict()
        new_page["assignment[description]"] = assignment["description"].replace(find_value, replace_value)

        # Now submit page back to canvas
        Canvas.update_assignment_for_course(course_id, assignment_id, new_page)

        pass


###### End CanvasAPIClass
