# -*- coding: utf-8 -*-

from gluon import *
from gluon import current
import json

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum, IntEnum

class LDAPEnum(Enum):
    ldaps = "ldaps://"
    ldap = "ldap://"

class SizeEnum(Enum):
    one_meg = 1024*1024
    gig1 = 1024*1024*1024

class ADConfig(BaseModel):
    ad_integration_enabled: bool = False
    ad_domain: str = "OPEDomain"
    ad_server: str = "ad.<base_domain>"
    laptop_ou: str = "OU=<program>,OU=<location>,OU=OPELaptops,<base_domain_dc>"
    faculty_group_ou: str = "OU=<location>,OU=FacultyGroups,<base_domain_dc>"
    faculty_user_ou: str = "OU=<location>,OU=Faculty,<base_domain_dc>"
    student_group_ou: str = "OU=<location>,OU=StudentGroups,<base_domain_dc>"
    student_user_ou: str = "OU=<location>,OU=Students,<base_domain_dc>"

    create_faculty_groups: bool = True
    create_student_groups: bool = True
    student_home_directory: str = ""
    faculty_home_directory: str = ""
    student_home_drive: str = ""
    faculty_home_drive: str = ""
    student_profile_directory: str = ""
    faculty_profile_directory: str = ""
    student_login_script: str = ""
    faculty_login_script: str = ""
    student_quota: int = "50000000"
    faculty_quota: int = "50000000000"

    ad_server_protocol: LDAPEnum = LDAPEnum.ldaps
    ad_service_user: str = "administrator"
    ad_service_password: str = ""

    file_server_enabled: bool = False
    file_server_service_user: str = "administrator"
    file_server_service_password: str = ""
    file_server_address: str = "files.<base_domain>"
    file_server_quota_drives: list[str] = []
class LaptopConfig(BaseModel):
    laptop_name_pattern: str = "OPELT_<user_id>"
    laptop_description: str = "<user_id> (<full_name>) - <laptop_serial_number> <credential_date>"
    add_local_admin_account: bool = False
    local_admin_user: str = "laptop_admin"
    local_admin_password: str = "dfslkjs<random>"

class LTIConfig(BaseModel):
    enabled: bool = True
    import_enabled: bool = True
    auto_create_courses: bool = True
    client_id: str = "OPE_LTI1_3_<base_domain>"
    deployment_id: str = "ope-lti-1_3-smc"
    issuer: str = "canvas.<base_domain>"
    public_key: str = ""
    private_key: str = ""
    show_media_library: bool = True
    show_document_library: bool = True
    show_help_library: bool = True

    canvas_server: str = "https://canvas.<base_domain>"
    canvas_access_token: str = "<ENV>"
    canvas_secret: str = "<ENV>"
    db_url: str = "postgresql"
    db_password: str = "<IT_PW>"
    student_quota: str = "1meg"
    faculty_quota: str = "1meg"
class SchoolConfig(BaseModel):
    school_name: str = ""
    app_description: str = ""
    base_domain: str = "ope.school.local"
    location: str = ""
    app_logo: str = ""
    prevent_students_changing_passwords: bool = True
    prevent_faculty_changing_passwords: bool = True
    disable_media_autoplay: bool = True
    prevent_media_search: bool = False
    prevent_document_search: bool = False
    student_userid_pattern: str = "s<user_id>"
    student_password_pattern: str = "Sid<user_id>!"
    faculty_userid_pattern: str = "<user_id>"
    faculty_password_pattern: str = "Fid<user_id>#"
    student_email_pattern: str = "<user_name>@student.<base_domain>"
    faculty_email_pattern: str = "<user_name>@<base_domain>"
    
    ad_config: ADConfig
    laptop_config: LaptopConfig
    lti_configs: list[LTIConfig]



# Settings Class
class AppSettings:

    def __init__(self):
        pass

    @staticmethod
    def SetValue(key, value):
        db = current.db # Grab current db object

        items = {key: value}
        db(db.my_app_settings).update(**items)
        db.commit()

    @staticmethod
    def GetValue(key, default):
        db = current.db  # Grab the current db object
        ret = ""

        settings = dict()

        if len(settings) < 1:
            # Need to load the settings
            rows = db(db.my_app_settings).select(limitby=(0, 1))
            for row in rows:
                for col in db.my_app_settings.fields:
                    settings[col] = row[col]
        
        if key in settings:
            if settings[key] is not None and len(str(settings[key])) > 0:
                ret = settings[key]  # t1
            else:
                ret = default
        else:
            ret = default
        
        # Test to see if this is a password that decoded properly - don't send back bad unicode passwords
        # Protects against 500 errors when enc key is wrong
        try:
            json.dumps(dict(k=ret))
        except UnicodeDecodeError:
            # This error means error decoding the value - common w decrypting with invalid key
            ret = default

        return ret
    
# End MySettings
