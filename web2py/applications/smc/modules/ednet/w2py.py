# -*- coding: utf-8 -*-

from gluon import *
from gluon import current

from .appsettings import AppSettings

# Web2PyAPIClass


class W2Py:
    def __init__(self):
        pass

    @staticmethod
    def Test():
        return "test"

    @staticmethod
    def SetStudentPassword(user_name, new_password, update_db=True):
        db = current.db
        ret = False
        # Get the auth_user id
        # USE LIKE TO SUPPORT CASE INSENSTIVE MATCHES
        rows = db(db.auth_user.username.like(user_name)).select()
        for row in rows:
            id = row['id']
            # Set password in info table
            if update_db is True:
                db(db.student_info.account_id == id).update(student_password=new_password)

            # Set Web2py password
            db(db.auth_user.id == id).update(password=db.auth_user.password.validate(new_password)[0])
            ret = True
        return ret
    
    @staticmethod
    def SetFacultyPassword(user_name, new_password, update_db=True):
        db = current.db
        ret = False
        #print("PW: " + user_name + str(update_db) + new_password)
        # Get the auth_user id
        # USE LIKE TO SUPPORT CASE INSENSTIVE MATCHES
        rows = db(db.auth_user.username.like(user_name)).select()
        for row in rows:
            id = row['id']
            # Set password in info table
            if update_db is True:
                db(db.faculty_info.account_id == id).update(faculty_password=new_password)

            # Set Web2py password
            db(db.auth_user.id == id).update(password=db.auth_user.password.validate(new_password)[0])
            ret = True
        return ret
    
    @staticmethod
    def CreateW2PStudentUser(user_name, password, user_email, first_name, last_name, user_ad_quota, user_canvas_quota,
                             row):
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object

        # Load the user if it already exists
        user = db(db.student_info.user_id == row.user_id).select().first()
        if user is None:
            # User doesn't exist, create it

            # Create the new user in web2py
            uid = db.auth_user.insert(last_name=last_name,
                                      first_name=first_name,
                                      username=user_name,
                                      password=db.auth_user.password.validate(password)[0],
                                      email=user_email
                                      )
            # Put the user in the students group
            auth.add_membership('Students', uid)

            default_ad_quota = user_ad_quota
            default_canvas_quota = user_canvas_quota

            # Move the rest of the info in place
            db.student_info.insert(
                account_id=uid,
                user_id=row.user_id,
                student_name=row.student_name,
                student_password=password,
                import_classes=row.import_classes,
                program=row.program,
                additional_fields=row.additional_fields,
                sheet_name=row.sheet_name,
                student_guid=row.student_guid,
                account_enabled=row.account_enabled,
                account_added_on=row.account_updated_on,
                account_updated_on=row.account_updated_on,
                student_ad_quota=default_ad_quota,
                student_canvas_quota=default_canvas_quota
                )
            pass
        else:
            # Student exists, update web2py info
            db(db.auth_user.id == user.account_id).update(
                                last_name=last_name,
                                first_name=first_name,
                                username=user_name,
                                # Don't overwrite existing password, GetPasswordForStudent
                                # Should have returned the current password so this is ok.
                                password=db.auth_user.password.validate(password)[0],
                                email=user_email
                                )

            # Update user info
            user.update_record(
                student_name=row.student_name,
                student_password=password,
                import_classes=row.import_classes,
                program=row.program,
                additional_fields=row.additional_fields,
                sheet_name=row.sheet_name,
                account_enabled=row.account_enabled,
                account_updated_on=row.account_updated_on,
                student_ad_quota=user_ad_quota,
                student_canvas_quota=user_canvas_quota
                )

            # Make sure the user in the students group
            auth.add_membership('Students', user.account_id)

        pass

    @staticmethod
    def CreateW2PFacultyUser(user_name, password, user_email, first_name, last_name, user_ad_quota, user_canvas_quota,
                             row):
        db = current.db  # Grab the current db object
        auth = current.auth  # Grab the current auth object

        # Load the user if it already exists
        user = db(db.faculty_info.user_id == row.user_id).select().first()
        if user is None:
            # User doesn't exist, create it

            # Create the new user in web2py
            uid = db.auth_user.insert(last_name=last_name,
                                      first_name=first_name,
                                      username=user_name,
                                      password=db.auth_user.password.validate(password)[0],
                                      email=user_email
                                      )
            # Put the user in the faculty group
            auth.add_membership('Faculty', uid)

            default_ad_quota = user_ad_quota
            default_canvas_quota = user_canvas_quota

            # Move the rest of the info in place
            db.faculty_info.insert(
                account_id=uid,
                user_id=row.user_id,
                faculty_name=row.faculty_name,
                faculty_password=password,
                import_classes=row.import_classes,
                program=row.program,
                additional_fields=row.additional_fields,
                sheet_name=row.sheet_name,
                faculty_guid=row.faculty_guid,
                account_enabled=row.account_enabled,
                account_added_on=row.account_updated_on,
                account_updated_on=row.account_updated_on,
                faculty_ad_quota=default_ad_quota,
                faculty_canvas_quota=default_canvas_quota
                )
            pass
        else:
            # User exists, update web2py info
            db(db.auth_user.id == user.account_id).update(
                                last_name=last_name,
                                first_name=first_name,
                                username=user_name,
                                # Don't overwrite existing password, GetPasswordForStudent
                                # Should have returned the current password so this is ok.
                                password=db.auth_user.password.validate(password)[0],
                                email=user_email
                                )

            # Update user info
            user.update_record(
                faculty_name=row.faculty_name,
                faculty_password=password,
                import_classes=row.import_classes,
                program=row.program,
                additional_fields=row.additional_fields,
                sheet_name=row.sheet_name,
                account_enabled=row.account_enabled,
                account_updated_on=row.account_updated_on,
                faculty_ad_quota=user_ad_quota,
                faculty_canvas_quota=user_canvas_quota
                )

            # Make sure the user in the faculty group
            auth.add_membership('Faculty', user.account_id)
        pass

# EndWeb2PyAPIClass
