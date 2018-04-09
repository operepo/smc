from gluon import *
from gluon import current
from datetime import datetime,timedelta

import sys

import ldap
#from .winrm import *
#from winrm import * as winrm
#from .. import winrm
import winrm
#from ..winrm.exceptions import WinRMTransportError
from winrm.exceptions import WinRMTransportError
#import applications.smc.modules.winrm
#from applications.smc.modules.winrm.exceptions import WinRMTransportError

from ednet.appsettings import AppSettings
from ednet.util import Util

###### ActiveDirectoryAPIClass

class AD:
    ### Config settings

    # Encoding to use
    _ad_encoding = "iso-8859-1" # "iso-8859-1"  "utf-8" "utf-16-le"

    # Active directory settings
    _ldap_enabled = False
    _ldap_protocol = ""
    _ldap_server = ""
    _ldap_login_user = ""
    _ldap_login_pass = ""

    # user and group paths
    _ad_student_cn = ""         # The container for students
    _ad_student_group_cn = ""   # The container for groups
    _ad_student_group_dn = ""   # The student group itself
    _ad_faculty_cn = ""
    _ad_faculty_group_cn = ""
    _ad_faculty_group_dn = ""

    # File server settings
    _file_server_import_enabled = False
    _file_server_address = ""
    _file_server_login_user = ""
    _flie_server_login_pass = ""

    # Quota settings
    _file_server_quota_drive = ""

    ### Static objects
    _init_run = False

    _ldap = None

    _winrm = None

    _errors = []

    def __init__(self):
        pass

    @staticmethod
    def Init():
        if (AD._init_run != True):
            AD._ad_encoding = "iso-8859-1"
            AD._ldap_enabled = AppSettings.GetValue('ad_import_enabled', False)
            AD._file_server_import_enabled = AppSettings.GetValue('file_server_import_enabled', False)
            AD._ldap_protocol = AppSettings.GetValue('ad_server_protocol', 'ldaps://')
            AD._ldap_server = AppSettings.GetValue('ad_server_address', 'ad.correctionsed.com')
            AD._ldap_login_user = AppSettings.GetValue('ad_service_user', 'Administrator')
            AD._ldap_login_pass = AppSettings.GetValue('ad_service_password', 'LDAP PASSWORD')
            AD._file_server_address = AppSettings.GetValue('file_server_address', '')
            AD._file_server_quota_drive = AppSettings.GetValue('file_server_quota_drive', 'c:')
            AD._file_server_login_user = AppSettings.GetValue('file_server_login_user', 'Administrator')
            AD._file_server_login_pass = AppSettings.GetValue('file_server_login_pass', 'Super Secret Password')

            #STUDENT SETTINGS

            AD._ad_student_cn = AppSettings.GetValue('ad_student_cn', 'OU=Students,DC=ad,DC=correctionsed,DC=com')
            AD._ad_student_group_cn = AppSettings.GetValue('ad_student_group_cn', 'OU=StudentGroups,DC=ad,DC=correctionsed,DC=com')
            AD._ad_student_group_dn = 'CN=Students,' + AD._ad_student_group_cn

            #FACULTY SETTINGS
            AD._ad_faculty_cn = AppSettings.GetValue('ad_faculty_cn', 'OU=Faculty,DC=ad,DC=correctionsed,DC=com')
            AD._ad_faculty_group_cn = AppSettings.GetValue('ad_faculty_group_cn', 'OU=FacultyGroups,DC=ad,DC=correctionsed,DC=com')
            AD._ad_faculty_group_dn = 'CN=Faculty,' + AD._ad_faculty_group_cn

            # Allow self signed certs and set options for AD
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

            AD._init_run = True

    @staticmethod
    def Close():
        if (AD._ldap != None):
            AD._ldap.unbind_s()

        AD._ldap = None
        AD._init_run = False
        AD._verify_ad_run = False
        AD._errors = []

    @staticmethod
    def Connect():
        ret = True
        if (AD.ConnectAD() != True):
            ret = False
        if (AD.ConnectWinRM() != True):
            ret = False
        return ret

    @staticmethod
    def ConnectAD():
        ret = False
        AD.Init()

        if (AD._ldap == None and AD._ldap_enabled == True):
            AD._ldap = ldap.initialize(AD._ldap_protocol + AD._ldap_server)
            AD._ldap.protocol_version = 3
            AD._ldap.set_option(ldap.OPT_REFERRALS, 0)

            try:
                #AD._ldap.simple_bind_s(AD._ldap_login_user, AD._ldap_login_pass)
                AD._ldap.simple_bind_s(AD._ldap_login_user.encode(AD._ad_encoding), AD._ldap_login_pass.encode(AD._ad_encoding))
                ret = True
            except ldap.INVALID_CREDENTIALS, message:
                err = """
<h1>Active Directory Login Error </h1>
<p style="font-size: 10px;">%s</p>
Active Directory is required to create user accounts for Windows. <br />
Please check your login credentials on the config page.<br />
For more information, please view the <a target='docs' href='""" % str(str(message) + " " + AD._ldap_server)
                err += URL('docs', 'ad', extension=False)
                err += "'>Active Directory Documentation Page</a><br/>"
                AD._errors.append(err)
                return False
            except ldap.SERVER_DOWN, message:
                err = """
<h1>Active Directory Connection error </h1>
<p style="font-size: 10px;">%s</p>
Active Directory is required to create user accounts for Windows. <br />
Please check your Active Directory server information on the config page and that your server is on.<br />
For more information, please view the <a target='docs' href='""" % str(str(message) + " " + AD._ldap_server)
                err += URL('docs', 'ad', extension=False)
                err += "'>Active Directory Documentation Page</a><br/>"
                AD._errors.append(err)
                return False
            except Exception, ex:
                # unkown error?
                err += "Unknown Error " + str(ex)
                AD._errors.append(err)
                return False
        else:
            ret = True
        return ret

    @staticmethod
    def ConnectWinRM():
        ret = False
        AD.Init()

        # Setup WinRM
        AD._winrm = winrm.Session(AD._file_server_address, auth=(AD._file_server_login_user, AD._file_server_login_pass))
        #AD._winrm = winrm.Session('http://' + AD._file_server_address + ':5985/wsman', auth=(AD._ldap_login_user, AD._ldap_login_pass))

        if (AD._file_server_import_enabled == True):
            try:
                r = AD._winrm.run_cmd('ipconfig', ['/all'])
                if (r.std_err != ""):
                    AD._errors.append("<b>Error testing WINRM connection:</b> " + str(r.std_err) + "<br />")
                    return False
            except WinRMTransportError, message:
                err = """
<h1>WINRM connection error </h1>
<p style="font-size: 10px;">%s</p>
WINRM is required to create home directories and set permissions. <br />
For more information, please view the <a target='docs' href='""" % str(str(message) + " " + AD._file_server_address)
                err += URL('docs', 'winrm', extension=False)
                err += "'>WinRM Documentation Page</a>\n<br />Done!"
                AD._errors.append(err)
                return False
            ret = True
        else:
            ret = True
        return ret

    @staticmethod
    def VerifyADSettings(auto_create = False):
        ret = True
        AD._errors = []
        AD.Close()
        con = AD.Connect()

        # Ensure that the proper items are present in the active directory structure
        if (AD._ldap_enabled != True):
            AD._errors.append("<B>Active Directory Disabled - Checks skipped</B>")
            return ret

        if (con == True):
            AD._errors.append("<b>AD Connection Successful</b> " + AD._ldap_server + "<br />")

        # STUDENT CHECKS
        # Check user cn exists
        cn = AD._ad_student_cn
        while ('<program>' in cn):
             cn = AD.GetParentLDAPPath(cn, 1)

        user_cn = AD.GetLDAPObject(cn)
        if (user_cn == None and auto_create == True):
            # Try and create it
            if (AD.CreateOU(cn) != True):
                AD._errors.append("<b>Error creating student OU: </b> " + cn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Student OU created: </b> " + cn + "<br />")
        elif (user_cn == None and auto_create != True):
            r = "<B>Student Container not present and auto create disabled! (" + cn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Student OU exists: </b> " + cn + "<br />")

        # Check that the groups cn exists
        group_cn = AD.GetLDAPObject(AD._ad_student_group_cn)
        if (group_cn == None and auto_create == True):
            if (AD.CreateOU(AD._ad_student_group_cn) != True):
                AD._errors.append("<b>Error creating student groups OU: </b> " + AD._ad_student_group_cn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Student groups OU created: </b> " + AD._ad_student_group_cn + "<br />")
        elif (group_cn == None and auto_create != True):
            r = "<B>Student Groups Container not present and auto create disabled! (" + AD._ad_student_group_cn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Student groups OU exists: </b> " + AD._ad_student_group_cn + "<br />")

        # Check that the students group exists
        student_group_dn = AD.GetLDAPObject(AD._ad_student_group_dn)
        if (student_group_dn == None and auto_create == True):
            if (AD.CreateGroup(AD._ad_student_group_dn) != True):
                AD._errors.append("<b>Error creating students group: </b> " + AD._ad_student_group_dn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Students group created: </b> " + AD._ad_student_group_dn + "<br />")
        elif (student_group_dn == None and auto_create != True):
            r = "<B>Students Group not present and auto create disabled! (" + AD._ad_student_group_dn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Students group exists: </b> " + AD._ad_student_group_dn + "<br />")

        # FACULTY CHECKS

        # Check user cn exists
        cn = AD._ad_faculty_cn
        while ('<program>' in cn):
             cn = AD.GetParentLDAPPath(cn, 1)

        user_cn = AD.GetLDAPObject(cn)
        if (user_cn == None and auto_create == True):
            # Try and create it
            if(AD.CreateOU(cn) != True):
                AD._errors.append("<b>Error creating faculty OU: </b> " + cn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Faculty OU created: </b> " + cn + "<br />")
        elif (user_cn == None and auto_create != True):
            r = "<B>Faculty Container not present and auto create disabled! (" + cn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Faculty OU exists: </b> " + cn + "<br />")

        # Check that the groups cn exists
        group_cn = AD.GetLDAPObject(AD._ad_faculty_group_cn)
        if (group_cn == None and auto_create == True):
            if (AD.CreateOU(AD._ad_faculty_group_cn) != True):
                AD._errors.append("<b>Error creating faculty groups OU: </b> " + AD._ad_faculty_group_cn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Faculty groups OU created: </b> " + AD._ad_faculty_group_cn + "<br />")
        elif (group_cn == None and auto_create != True):
            r = "<B>Faculty Groups Container not present and auto create disabled! (" + AD._ad_faculty_group_cn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Faculty groups OU exists: </b> " + AD._ad_faculty_group_cn + "<br />")

        # Check that the faculty group exists
        faculty_group_dn = AD.GetLDAPObject(AD._ad_faculty_group_dn)
        if (faculty_group_dn == None and auto_create == True):
            if (AD.CreateGroup(AD._ad_faculty_group_dn) != True):
                AD._errors.append("<b>Error creating faculty group: </b> " + AD._ad_faculty_group_dn + "<br />")
                ret = False
            else:
                AD._errors.append("<b>Faculty group created: </b> " + AD._ad_faculty_group_dn + "<br />")
        elif (faculty_group_dn == None and auto_create != True):
            r = "<B>Faculty Group not present and auto create disabled! (" + AD._ad_faculty_group_dn + ")<br/>"
            AD._errors.append(r)
            ret = False
        else:
            AD._errors.append("<b>Faculty group exists: </b> " + AD._ad_faculty_group_dn + "<br />")

        return ret

    @staticmethod
    def CreateGroup(group_dn):
        ret = False
        if (AD.Connect() != True):
            return ret

        if (group_dn == ""):
            AD._errors.append("<b>Invalid Group CN: </b>" + str(group_dn) + "<br />")
            return ret

        if (AD.GetLDAPObject(group_dn) != None):
            #AD._errors.append("<b>Group already exists: </b> " + str(group_dn) + "<br />")
            return True

        # Get the sAMAccountName name from the DN
        parts = group_dn.split(',')
        gname = ""
        if (len(parts) > 0):
            parts = parts[0].split('=')
        else:
            AD._errors.append("<b>Invalid Group DN! </b>" + str(group_dn) + "<br />")
            return ret
        if (len(parts) == 2):
            gname = parts[1]
        else:
            AD._errors.append("<b>Invalid Group DN! </b>" + str(group_dn) + "<br />")
            return ret

        if (gname == ""):
            AD._errors.append("<b>Invalid Group DN! </b>" + str(group_dn) + "<br />")
            return ret

        group_attrs = {}
        group_attrs['objectClass'] = ['top', 'group']
        #group_attrs['cn'] = 'Students'
        #group_attrs['groupType'] = "0x80000002"
        #group_attrs['name'] = 'Students'
        #group_attrs['objectCategory'] = 'CN=Group,CN=Schema,CN=Configuration,DC=cbcc,DC=pencollege,DC=net'
        group_attrs['sAMAccountName'] = gname.encode(AD._ad_encoding)
        group_ldif = Util.GetModList(group_attrs, None)

        try:
            AD._ldap.add_s(group_dn.encode(AD._ad_encoding), group_ldif)
            ret = True
        except ldap.LDAPError, error_message:
            AD._errors.append("<B>Error creating group:</b> " + str(group_dn) + "<br />")
        return ret

    @staticmethod
    def AddUserToGroup(user_dn, group_dn):
        ret = False

        if (AD.Connect() != True):
            return ret

        add_member = [(ldap.MOD_ADD, 'member', user_dn.encode(AD._ad_encoding))]
        try:
            AD._ldap.modify_s(group_dn.encode(AD._ad_encoding), add_member)
            ret = True
        except ldap.LDAPError, error_message:
            if (error_message[0]['desc'] == 'Already exists'):
                # Ignore if user is already in the group
                ret = True
                pass
            else:
                AD._errors.append("<B>Error adding user (" + str(user_dn) + ") to group (" + str(group_dn) + ")</b> %s" % error_message)

        return ret

    @staticmethod
    def GetNameFromLDAPPath(path):
        ret = ""
        # Get the name for the OU
        parts = path.split(',')
        ld_name = ""
        if (len(parts) > 0):
            parts = parts[0].split('=')
        else:
            AD._errors.append("<b>Invalid LDAP Path! </b>" + str(path) + "<br />")
            return ret
        if (len(parts) == 2):
            ld_name = parts[1].strip()
        else:
            AD._errors.append("<b>Invalid LDAP Path! </b>" + str(path) + "<br />")
            return ret

        if (ld_name == ""):
            AD._errors.append("<b>Invalid LDAP Path! </b>" + str(path) + "<br />")
            return ret
        ret = ld_name
        return ret

    @staticmethod
    def GetParentLDAPPath(cn, levels=1):
        ret = cn

        if (levels > 0):
            levels -= 1
            parts = cn.split(',')
            ret = ','.join(parts[1:])
            if (levels > 0):
                ret = AD.GetParentLDAPPath(ret, levels)

        return ret

    @staticmethod
    def GetDN(object_name, container_cn):
        new_dn = 'cn=' + object_name + "," + container_cn
        return new_dn

    @staticmethod
    def CreateOU(ou_dn):
        ret = False
        if (AD.Connect() != True):
            return ret

        if (ou_dn == ""):
            AD._errors.append("<b>Invalid OU: </b>" + str(ou_dn) + "<br />")
            return ret

        ou = AD.GetLDAPObject(ou_dn)
        if (ou != None):
            #AD._errors.append("<b>OU Already exists:</b> " + str(ou_dn) + "<br />")
            return True

        ou_name = AD.GetNameFromLDAPPath(ou_dn)

        ou_attrs = {}
        ou_attrs['objectClass'] = ['top', 'organizationalUnit']
        ou_attrs['name'] = ou_name.encode(AD._ad_encoding)

        ou_ldif = Util.GetModList(ou_attrs, None)

        try:
            AD._ldap.add_s(ou_dn.encode(AD._ad_encoding), ou_ldif)
            ret = True
        except ldap.LDAPError, error_message:
            AD._errors.append("<B>Error creating OU:</b> " + str(ou_dn) + "<br />")
        return ret

    @staticmethod
    def MakePathCN(cn):
        ret = False
        log = ""

        parts = cn.split(',')
        dc = ""
        # Get the DC entries
        while (len(parts)> 0):
            item = parts.pop()
            if ('dc=' in item.lower()):
                if (dc != ""):
                    dc = "," + dc
                dc = item + dc
            else:
                parts.append(item)
                break

        # Now make sure each OU exists
        last_cn = dc
        while (len(parts) > 0):
            item = parts.pop()
            cn = item + "," + last_cn
            last_cn = cn
            log += " - " + cn
            ret = AD.CreateOU(cn)
        ret = log
        return ret

    @staticmethod
    def CreateUser(user_name, container_cn):
        ret = False
        if (AD.ConnectAD() != True):
            return ret

        # Make sure the container exists
        if (AD.MakePathCN(container_cn) == False):
            AD._errors.append("<b>Error making OU path: </b>" + str(container_cn))
            return ret

        #TODO - Detect user in different OU and move it?
        new_user_dn = AD.GetDN(user_name, container_cn)
        user = AD.GetLDAPObject(new_user_dn, True)
        if (user != None):
            # User already exists
            # Do we need to move the user?
            curr_dn = user[0][1]['distinguishedName'][0]
            if (curr_dn.lower() != new_user_dn.lower()):
                # Rename to move
                try:
                    AD._ldap.rename_s(curr_dn.encode(AD._ad_encoding), "cn=" + user_name.encode(AD._ad_encoding), container_cn.encode(AD._ad_encoding))
                except ldap.LDAPError, error_message:
                    AD._errors.append("<b>Error moving user to new OU</b> " + str(user_name) + " %s" % error_message)
                    return False
            return True

        user_attrs = {}
        user_attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
        user_attrs['sAMAccountName'] = user_name.encode(AD._ad_encoding)
        uac = 514 # normal user account
        user_attrs['userAccountControl'] = str(uac).encode(AD._ad_encoding)
        user_ldif = Util.GetModList(user_attrs, None)

        try:
            AD._ldap.add_s(new_user_dn.encode(AD._ad_encoding), user_ldif)
        except ldap.LDAPError, error_message:
            AD._errors.append("<b>Add User Error:</b> " + str(user_name) + " %s" % error_message)

        if (AD.GetLDAPObject(new_user_dn) != None):
            # User is created and present
            ret = True
        return ret

    @staticmethod
    def UpdateUserInfo(user_dn, email_address="", first_name="", last_name="", display_name="", description="", id_number="", home_drive_letter="", home_directory="", login_script="", profile_path="",  ts_allow_login='FALSE'):
        ret = True
        if (AD.ConnectAD() != True):
            return False

        if (AD.GetLDAPObject(user_dn) == None):
            # User doesn't exist
            AD._errors.append("<B>Error changing user that doesn't exist (" + str(user_dn) + ")")
            return False

        u_attrs = {}
        u_attrs['userPrincipalName'] = email_address.encode(AD._ad_encoding)
        u_attrs['givenName'] = first_name.encode(AD._ad_encoding)
        u_attrs['sn'] = last_name.encode(AD._ad_encoding)
        u_attrs['displayName'] = display_name.encode(AD._ad_encoding)
        u_attrs['description'] = description.encode(AD._ad_encoding)
        u_attrs['mail'] = email_address.encode(AD._ad_encoding)
        u_attrs['employeeID'] = id_number.encode(AD._ad_encoding)
        u_attrs['msTSAllowLogon'] = 'FALSE'
        u_ldif = Util.GetModList(u_attrs, ldap.MOD_REPLACE)

        # Update Base info
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), u_ldif)
        except ldap.LDAPError, error_message:
            AD._errors.append("<b>Error updating user: " + str(user_dn) + " %s" % error_message)
            ret = False

        # Set drive letter
        home_drive = [(ldap.MOD_REPLACE, 'homeDrive', [home_drive_letter.encode(AD._ad_encoding)])]
        if (home_drive_letter == ''):
            home_drive = [(ldap.MOD_DELETE, 'homeDrive', None)]
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), home_drive)
        except ldap.LDAPError, error_message:
            if (error_message[0]['desc'] == 'No such attribute'):
                # Ignore error if attribute is already gone
                pass
            else:
                AD._errors.append("<b>Error updating user:</b> " + str(user_dn) + " %s" % error_message)
                ret = False

        # Set home directory
        home_dir = [(ldap.MOD_REPLACE, 'homeDirectory', [home_directory.encode(AD._ad_encoding)])]
        if (home_directory == ''):
            home_dir = [(ldap.MOD_DELETE, 'homeDirectory', None)]
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), home_dir)
        except ldap.LDAPError, error_message:
            if (error_message[0]['desc'] == 'No such attribute'):
                # Ignore error if attribute is already gone
                pass
            else:
                AD._errors.append("<b>Error setting home directory:</b> %s" % error_message)
                ret = False

        # Save login script path
        script_path = [(ldap.MOD_REPLACE, 'scriptPath', [login_script.encode(AD._ad_encoding)])]
        if (login_script == ''):
            script_path = [(ldap.MOD_DELETE, 'scriptPath', None)]
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), script_path)
        except ldap.LDAPError, error_message:
            if (error_message[0]['desc'] == 'No such attribute'):
                # Ignore error if attribute is already gone
                pass
            else:
                AD._errors.append("<b>Error setting script directory:</b> %s" % error_message)
                ret = False

        # Save Profile Path
        profile = [(ldap.MOD_REPLACE, 'profilePath', [profile_path.encode(AD._ad_encoding)])]
        if (profile_path == ''):
            profile = [(ldap.MOD_DELETE, 'profilePath', None)]
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), profile)
        except ldap.LDAPError, error_message:
            if (error_message[0]['desc'] == 'No such attribute'):
                # Ignore error if attribute is already gone
                pass
            else:
                AD._errors.append("<b>Error setting profile directory:</b> %s" % error_message)
                ret = False

        return ret
    
    @staticmethod
    def SetPassword(user_dn, password):
        ret = False

        if (AD.ConnectAD() != True):
            return ret

        if (AD.GetLDAPObject(user_dn) == None):
            AD._errors.append("<B>Error setting password for nonexisting user:</b> " + str(user_dn))
            return ret

        unicode_pw = unicode('\"' + password + '\"', 'iso-8859-1')
        password_value = unicode_pw.encode('utf-16-le')
        add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]
        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), add_pass)
            #AD._errors.append("<b>Setting password: </b> " + str(user_dn))
        except ldap.LDAPError, error_message:
            AD._errors.append("<b>Error setting pasword for user:</b> " + str(user_dn) + " %s" % error_message)
            return ret
        return True

    @staticmethod
    def EnableUser(user_dn, enabled=True):
        ret = False
        if (AD.ConnectAD() != True):
            return ret

        if (AD.GetLDAPObject(user_dn) == None):
            AD._errors.append("<b>Can't enable user that doesn't exist: </b> " + str(user_dn))
            return ret

        uac = 0x10200 # normal account, enabled, don't expire password
        if (enabled != True):
            uac = 0x10202 # normal account, DISABLED, don't expire password
        mod_acct = [(ldap.MOD_REPLACE, 'userAccountControl', str(uac).encode(AD._ad_encoding))]

        try:
            AD._ldap.modify_s(user_dn.encode(AD._ad_encoding), mod_acct)
            ret =  True
        except ldap.LDAPError, error_message:
            AD._errors.append("<b>Error enabling/disabling user: </b>" + str(user_dn))
            return ret

        return ret

    @staticmethod
    def DisableUser(user_dn):
        return AD.EnableUser(user_dn, False)

    @staticmethod
    def GetLastLoginTime(user_dn):
        ret = None
        
        if (user_dn == None):
            AD._errors.append("GetLastLoginTime: Missing user_dn" )
            return None # "Invalid UserDN (None)"
        
        if (AD.ConnectAD() != True):
            ret = None
            return ret

        #ret = "Getting: " + user_dn
        u = AD.GetLDAPObject(user_dn, search_parent=False, ret_arr=['lastLogon']) #['distinguishedName'])
        if (u == None):
            u = AD.GetLDAPObject(user_dn, search_parent=True, ret_arr=['lastLogon']) #['distinguishedName'])
        if (u == None):
            # Couldn't find student
            AD._errors.append("GetLastLoginTime: Invalid UesrDN " + str(user_dn) )
            return None
        #try:
        r = u[0][1]['lastLogon'][0]
        if (r==None):
            ret = None
        elif (str(r) == "0"):
            ret = None
        else:
            ansiTimeStart = datetime(1601,1,1)
            sec = (long(r) / 10000000)
            lastLogin = timedelta(seconds=long(r) / 10000000)
            tzoffset = datetime.now() - datetime.utcnow()
            #ret += "[" + str(sec) + "]"
            #rfc822- with borked timezone
            #rfc = (ansiTimeStart+lastLogin).strftime("%a, %d %b %Y %H:%M:%S +0000")
            #iso 8601
            #iso = (ansiTimeStart+lastLogin).isoformat()
            # Pretty
            
            ret = (ansiTimeStart+lastLogin+tzoffset) #.strftime("%a %d %b %Y %I:%M:%S %p %Z")
        #except Exception, e:
        #    #ret = None
        #    (t, v, tb) = sys.exc_info()
        #    AD._errors.append("GetLastLoginTime: Exception " + str(e) + " " + str(user_dn) + str(tb) + "|||" )
        #    #ret = " Error getting login time " + str(e) + " " + user_dn
        #ret += AD.GetErrorString()
        return ret
    
    @staticmethod
    def GetLDAPObject(cn, search_parent=False, ret_arr=['distinguishedName']):
        ret = None
        if (AD.ConnectAD() != True):
            return ret
        
        # Make sure that ['distinguishedName'] is in the ret_arr
        #AD._errors.append(str(ret_arr))
        if (ret_arr == None):
            #AD._errors.append("NONE")
            ret_arr = ['distinguishedName']
        if ('distinguishedName' in ret_arr):
            #AD._errors.append("DN present")
            pass
        else:
            #AD._errors.append("DN Not Present")
            ret_arr.append('distinguishedName')
        #AD._errors.append(str(ret_arr))
        
        cn_name = AD.GetNameFromLDAPPath(cn)

        if (search_parent == True):
            cn = AD.GetParentLDAPPath(cn, 2)
        else:
            cn = AD.GetParentLDAPPath(cn, 1)
        #AD._errors.append("Searching " + str(cn) + " for " + cn_name)
        try:
            #r = AD._ldap.search_s(cn, ldap.SCOPE_BASE, "(name=" + str(cn_name) + ")" , ['distinguishedName'])
            r = AD._ldap.search_s(cn.encode(AD._ad_encoding), ldap.SCOPE_SUBTREE, "(name=" + str(cn_name).encode(AD._ad_encoding) + ")" , ret_arr) # ['distinguishedName'])
            if (len(r) != 0 and isinstance(r[0][1], dict) and r[0][1]['distinguishedName'][0] != ''):
                ret = r
            else:
                # Try sAMAccountName Search...
                r = AD._ldap.search_s(cn.encode(AD._ad_encoding), ldap.SCOPE_SUBTREE, "(sAMAccountName=" + str(cn_name).encode(AD._ad_encoding) + ")" , ret_arr) # ['distinguishedName'])
                if (len(r) != 0 and isinstance(r[0][1], dict) and r[0][1]['distinguishedName'][0] != ''):
                    ret = r
        except ldap.LDAPError, error_message:
            #r = "Exception: CN (" + cn + ") does not exist! %s" % error_message
            #AD._errors.append(r)
            pass
        return ret

    @staticmethod
    def GetErrorString():
        ret = ""
        for error in AD._errors:
            ret += "<div class=error_string>" + str(error) + "</div>"
        return ret

    @staticmethod
    def CreateHomeDirectory(user_name, folder_path):
        ret = ""
        if (AD.Connect() != True):
            AD._errors.append("<b>WinRM Not Connected!</b>")
            ret = AD.GetErrorString()
            return ret

        if (AD._file_server_import_enabled != True):
            return "AD Disabled" # Return true if disabled since it isn't an error

        try:
            # Create the folder
            r = AD._winrm.run_cmd('mkdir', ['"' + folder_path + '"'])
            err = r.std_err.strip()
            # TODO DEBUG - Grab output and debug commands
            ret += r.std_out + " err: " + err
            if (err != "" and err.endswith("already exists.") != True):
                AD._errors.append("<b>Error creating home directory:</b> " + str(r.std_err) + "<br />")

            # Set permissions
            r = AD._winrm.run_cmd('icacls', ['"' + folder_path + '"',
                "/grant", '"' + user_name + ':(OI)(CI)(DE,GR,GW,GE,RD,WD,AD,X,DC,RA)"', "/inheritance:e",
                "/T", "/C", "/Q" ]) # "/T"
            ret += r.std_out + " err: " + r.std_err
            if (r.std_err != ""):
                AD._errors.append("<b>Error setting permissions on home directory:</b> " + str(r.std_out) + " - " + str(r.std_err) + "<br />")
        except:
            er = "<b>Error creating home folder: </b> " + str(folder_path)
            ret += er
            AD._errors.append(er)

        return ret

    @staticmethod
    def SetDriveQuota(user_name, quota):
        ret = False
        out = ""

        if (AD.Connect() != True):
            return ret

        if (AD._file_server_import_enabled != True or quota == "" or AD._file_server_quota_drive == ""):
            return True # Return true if disabled since it isn't an error

        try:
            # Calculate the warning level
            warning_level = int(int(quota) * .80)

            # Set the quota
            r = AD._winrm.run_cmd('fsutil', [ 'quota', 'modify', AD._file_server_quota_drive, str(warning_level), str(quota), user_name])
            if (r.std_err != ""):
                AD._errors.append("<b>Error setting quota:</b> " + str(r.std_out) + " - " + str(r.std_err) + "<br />")
            #AD._errors.append("Quota: " + str(r.std_out) + str(r.std_err) + " " + user_name)
            ret = True
        except:
            er = "<b>Error setting drive quota: </b> " + str(user_name) + ":" + str(quota)
            AD._errors.append(er)

        return ret

    @staticmethod
    def SetQuotaEnabled(enable=True, enforce=True):
        ret = True

        if (AD.Connect() != True):
            return ret

        if (AD._file_server_import_enabled != True or AD._file_server_quota_drive == ""):
            return True # Return true if disabled since it isn't an error

        try:
            if (enable == True and enforce == True):
                r = AD._winrm.run_cmd('fsutil', ['quota', 'enforce', AD._file_server_quota_drive])
                if (r.std_err != ""):
                    AD._errors.append("<b>Error enabling quota:</b> " + str(r.std_out) + " - " + str(r.std_err) + "<br />")

            if (enable == True and enforce != True):
                r = AD._winrm.run_cmd('fsutil', ['quota', 'track', AD._file_server_quota_drive])
                if (r.std_err != ""):
                    AD._errors.append("<b>Error enabling quota:</b> " + str(r.std_out) + " - " + str(r.std_err) + "<br />")

            if (enable == False):
                r = AD._winrm.run_cmd('fsutil', ['quota', 'disable', AD._file_server_quota_drive])
                if (r.std_err != ""):
                    AD._errors.append("<b>Error disabling quota:</b> " + str(r.std_out) + " - " + str(r.std_err) + "<br />")

            ret = True
        except:
            er = "<b>Error changing quota settings: </b> " + str(user_name) + ":" + str(quota)
            AD._errors.append(er)

        return ret

###### End ActiveDirectoryAPIClass
