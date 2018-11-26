# -*- coding: utf-8 -*-
# try something like

#from ednet.ad import AD
from ednet import Util, SequentialGUID, AppSettings, W2Py, Student
#from ednet import *
from ednet.ad import AD
from ednet.faculty import Faculty
from ednet.util import Util
from ednet.canvas import Canvas
from pytube import YouTube
import os
import ssl

# import ldap
import ldap3


import sys

auth.settings.allow_basic_login = True


@auth.requires_membership("Administrators")
def basic_auth_test():
    h = request.headers
    b_auth = h["Authorization"]

    return locals()


@auth.requires_membership("Administrators")
def ad_test():
    # ad_pw = AppSettings.GetValue("ad_service_password", "NOT FOUND")
    # file_pw = AppSettings.GetValue("file_server_login_pass", "NOT FOUND")
    # c = AD.Connect()

    # Keep this off - exposes too much
    # ld = AD._ldap

    # whoami = AD._ldap.extend.standard.who_am_i()

    cn_name = "s777777"
    dn = "cn=s777777,ou=cse,ou=students,dc=pencol,dc=local"
    container_dn = "ou=cse,ou=students,dc=pencol,dc=local"

    current_enrollment = Canvas.GetCurrentClasses(cn_name)
    courses = {}
    for e in current_enrollment:
        courses[e['id']] = e['updated_at']

    # create_user = AD.CreateUser(cn_name, container_dn)
    # Student.SetPassword("777777", "Sid777777!")

    # update_user = AD.UpdateUserInfo(dn, email_address="test@test", first_name="test", last_name="smith",
    #                                 display_name="testing", description="this is a test", id_number="10",
    #                                 home_drive_letter="W", home_directory="c:\home",
    #                                 login_script="login_script", profile_path="pfpath",
    #                                 ts_allow_login='FALSE')


    # Test - Enable user
    # disable = AD.DisableUser(dn)
    # enable = AD.EnableUser(dn)
    # Student.EnableAccount("777777")

    # r = AD._ldap.search(dn.encode(AD._ad_encoding),
    #                    "(name=" + str(cn_name).encode(AD._ad_encoding) + ")",
    #                    search_scope=ldap3.SUBTREE,
    #                   attributes=['distinguishedName'],
    #                    )
    # s = AD._ldap.response
    # ret_arr)  # ['distinguishedName'])

    # ret = AD.VerifyADSettings(False)



    #last_login_time = AD.GetLastLoginTime(dn)

    #grp_dn = "cn=test_group,OU=StudentGroups,DC=pencol,DC=local"
    #cg = AD.CreateGroup(grp_dn)

    #add_to_group = AD.AddUserToGroup(dn, grp_dn)

    #t_ou_dn = "OU=test_OU,DC=pencol,DC=local"
    #test_ou = AD.CreateOU(t_ou_dn)


    err = AD._errors

    return locals()

@auth.requires_membership("Administrators")
def test():

    #db_canvas = current.db_canvas
    #sql = "select * from users"
    #rows = db_canvas.executesql(sql)
    #test = Canvas.EnsureAdminAccessToken()
    #student_test = Canvas.EnsureStudentAccessToken("s777777")

    initial_run = cache.ram("startup", lambda:True, time_expire=3600)
    cache_time = cache.ram("tmptime", lambda:time.ctime(), time_expire=30)
    return locals()

@auth.requires_membership("Administrators")
def index():
    
    yt = YouTube()
    
    # Set the video URL.
    ret = ""
    tmpurl = "http://youtu.be/BthR2vlqrLo!!1"
    tmpurl = tmpurl.replace("/embed/", "/watch?v=")
    yt.url = tmpurl
    
    ret += str(yt.videos)
    yt.filename = "tempvid"
    # Get the highest res mp4
    ret += str(type(yt.filter('mp4')))
    f = yt.filter('mp4')[-1]
    
    try:
        f.download()
    except Exception as e:
        ret += str(e)
    
    #test = {}
    #ret = isinstance(test, dict)
    
    #AD.Connect()
    

    #cn="cn=ropulsipher,OU=CSE,OU=Faculty,DC=cbcc,DC=pencollege,DC=net"
    #cn_name = AD.GetNameFromLDAPPath(cn)
    
    #ret = ""
    
    #p1 = AD.GetParentLDAPPath(cn, 1)
    #p2 = AD.GetParentLDAPPath(cn, 2)
    
    #r = AD._ldap.search_s(p2, ldap.SCOPE_SUBTREE, "(name=" + str(p2) + ")" , ['distinguishedName'])
    #AD._errors.append("Found Object : " + str(r))
    
    #cn = "OU=CSE," + cn
    #ret = AD.MakePathCN(cn)
    
    #ret = AD.CreateUser('walshb', cn)
    
    #errors = AD._errors
    
    #AD.Close()
    
    #path = sys.path
    #a = Util.ParseName("bob smith")
    #b = Student.GetQuota("777777")

    #c = Student.QueueActiveDirectoryImports("SIMPLE SHEET")
    #d = Student.ProcessADStudent()

    #e = AD.GetCN("OU=Students,DC=cbcc,DC=pencollege,DC=net")
    #f = AD.GetCN("CN=s777777,OU=Students,DC=cbcc,DC=pencollege,DC=net")
    #createou = AD.CreateOU("OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    #creategroup = AD.CreateGroup("CN=TestGroup,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    #createdn = AD.GetDN("1st", "2nd")
    #createuser = AD.CreateUser("s777777", "OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    #addtogroup = AD.AddUserToGroup("CN=s777777,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net", "CN=TestGroup,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    #setpassword = AD.SetPassword("CN=s777777,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net", "SID7777772")    
    #enableuser = AD.EnableUser("CN=s777777,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    #updateuser = AD.UpdateUserInfo("CN=s777777,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net", "s777777@cored.com", "bob", "smith", "smith, bob", description="Student account", id_number="s777777", home_drive_letter="", home_directory="", login_script="", profile_path="",  ts_allow_login='FALSE')
    #disableuser = AD.DisableUser("CN=s777777,OU=StudentsTest,DC=cbcc,DC=pencollege,DC=net")
    
    #setpass = AD.SetPassword("CN=s777780,OU=Students,DC=cbcc,DC=pencollege,DC=net", "123f")
    
    #groupdn = AD.GetLDAPObject("CN=Students,OU=StudentGroups,DC=cbcc,DC=pencollege,DC=net")
    #cn = AD.GetLDAPObject("OU=StudentGroups,DC=cbcc,DC=pencollege,DC=net")
    #setpass = Faculty.SetPassword("walshb", "12345612ABC")
    #ad_errors = AD._errors

    return dict(vars=locals())
