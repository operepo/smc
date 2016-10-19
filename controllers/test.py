# -*- coding: utf-8 -*-
# try something like

#from ednet.ad import AD
#from ednet import Util, SequentialGUID, AppSettings, W2Py, Student
#from ednet import *
from ednet.ad import AD
from ednet.faculty import Faculty
from ednet.util import Util

from pytube import YouTube
import os

import ldap

import sys

def test():
    a = os.environ["IT_PW"]
    return locals()

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
    except Exception, e:
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
