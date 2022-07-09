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

# Help shut up pylance warnings
if 1==2: from ..common import *

# import ldap
# import ldap
import ssl
from ldap3 import Server, Connection, ALL, NTLM, Tls
import ldap3.core.exceptions
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups
from ldap3.utils.dn import safe_rdn


import sys

auth.settings.allow_basic_login = True

# Always reload modules on the test controller
import module_reload
ret = module_reload.ReloadModules()

@auth.requires_membership("Administrators")
def test_parse_names():
    response.view = 'generic.json'
    ret = dict()

    name1 = "Twiringiyimana, Viater"
    name2 = "Magana-Sanchez, Juan Manuel"

    ret[name1] = Util.ParseName(name1)
    ret[name2] = Util.ParseName(name2)


    return ret

@auth.requires_membership("Administrators")
def test_cleanup_youtube_urls():
    response.view = 'generic.json'
    ret = dict()

    cleanup_youtube_urls()
    ret["Result"] = "Done."

    return ret


@auth.requires_membership("Administrators")
def test_scheduler_process_videos():
    response.view = 'generic.json'
    ret = dict()
    ts = db_scheduler(
        (db_scheduler.scheduler_task.task_name=='process_youtube_queue') &
        ((db_scheduler.scheduler_task.status=='QUEUED') | (db_scheduler.scheduler_task.status=='RUNNING'))
        ).select(orderby=~db_scheduler.scheduler_task.id).first()
    ret["ts"] = ts
    return ret

@auth.requires_membership("Administrators")
def test_youtube_captions():
    response.view = 'generic.json'
    ret = dict()

    yt_url = "https://www.youtube.com/watch?v=mn98cBZBg7s"

    #yt, stream, res = find_best_yt_stream(yt_url)
    #ret["captions"] = str(yt.captions)
    pull_youtube_caption(yt_url, "db5f752fa6d74e76b725c788ed62607b")


    return ret

@auth.requires_membership("Administrators")
def test_youtube():
    response.view = 'generic.json'
    ret = dict()
    

    yt_url = "https://www.youtube.com/watch?v=jAMGMKlBSV0"

    yt, stream, res = find_best_yt_stream(yt_url)
    ret['yt'] = str(yt)
    ret['stream'] = str(stream)
    ret['res'] = str(res)

    (w2py_folder, applications_folder, app_folder) = get_app_folders()
    target_folder = os.path.join(app_folder, 'static', 'media')
    output_mp4_filename = "test.mp4"

    print("Downloading " + str(yt_url)+"\n\n")
    stream.download(output_path=target_folder, filename=output_mp4_filename)  # put in folder name
    print("\nDownload Complete!")

    return ret


@auth.requires_membership("Administrators")
def test_imscc_import():
    response.view = 'generic.json'
    
    if Canvas.Connect() is not True:
            return dict(error="Couldn't Connect to Canvas!")
    
    #access_token = AppSettings.GetValue('canvas_access_token', '')
    import urllib
    
    source_url = "http://gateway.<DOMAIN>/migrations/" + urllib.parse.quote("course_file.imscc")
    course_id = "502033000000079"
            
    p = dict()
    p["migration_type"] = "canvas_cartridge_importer"
    p["settings[file_url]"] = source_url
    
    new_migration = None
    new_migration = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token,
                                     "/api/v1/courses/" + course_id + "/content_migrations",
                                      method="POST", params=p)
    
    ret = dict()
    ret["url"] = Canvas._canvas_server_url
    ret["output"] = str(new_migration)
        
    return ret

@auth.requires_membership("Administrators")
def test_streamlink():
    import streamlink

    streams = streamlink.streams("https://www.youtube.com/watch?v=T9gewxW9zVY")
    trys = ['720p', '360p', 'best', 'worst']
    stream = streams['720p']


    return dict(s=stream)

@auth.requires_membership("Administrators")
def test_yt_proxies():
    response.view = 'generic.json'

    ret = get_youtube_proxies()
    
    return ret

@auth.requires_permission("credential")
def credential():
    return dict(message="It Worked!")

@auth.requires_membership("Administrators")
def test_credential():
    a_id = auth.id_group("Administrators")
    f_id = auth.id_group("Faculty")

    auth.add_permission(name='credential', group_id=a_id)
    auth.add_permission(name='credential', group_id=f_id)


    return locals()

@auth.requires_membership("Administrators")
def dev_key_test():
    
    response.view = 'generic.json'
    (dev_key_id, msg) = Canvas.EnsureDevKey()
    return locals()

@auth.requires_membership("Administrators")
def winrm_test():
    ret = ""

    r = AD.ConnectWinRM()
    errors = AD._errors

    return locals()


@auth.requires_membership("Administrators")
def load_document_json():
    document_id = "748a804ba39d4146841010df81eff057"

    ret = load_document_file_json(document_id)
    return locals()

@auth.requires_membership("Administrators")
def next_test():
    
    
    # Get the users to import
    sheet_name = "STUDENT USERS"
    #rows = db(db.student_import_queue.sheet_name == sheet_name).select()
    #rows = db(db.student_info).select()
    #for row in rows:
    
    #_ad_encoding = "iso-8859-1" 
    
    #_ldap = Connection(AD._ldap_session, "huskers",
    #                                  "testing",
    #                                  authentication=ldap3.NTLM,
    #                                  auto_bind=True,
    #                                  raise_exceptions=True,
    #                                  auto_referrals=False,
    #                                  client_strategy=ldap3.RESTARTABLE,
    #                                  #receive_timeout=60,
    #                                  
    #                                  )
    
    AD.ConnectAD()
    
    return locals()

@auth.requires_membership("Administrators")
def checkbox_test():
    form3 = FORM(TABLE(
                       TR(XML("Write Changes <span style='color: red; font-size:10px;'>" +
                              "(check this to update canvas)</span>: "),
                          INPUT(_type="checkbox", _name="write_changes", value="")),
                       TR(INPUT(_type="submit", _value="GO"))
                       ),
                 #_action=URL('test', 'checkbox_test.load'),
                 _name="form3").process(keepvalues=True, formname="form3")

    write_changes = None

    if form3.accepted:
        write_changes = form3.vars.write_changes
        # if form3.vars.write_changes is True:
        #    write_changes = True

    return dict(form3=form3, write_changes=write_changes)


@auth.requires_membership("Administrators")
def basic_auth_test():
    h = request.headers
    b_auth = h["Authorization"]

    return locals()


@auth.requires_membership("Administrators")
def ad_test():
    # ad_pw = AppSettings.GetValue("ad_service_password", "NOT FOUND")
    # file_pw = AppSettings.GetValue("file_server_login_pass", "NOT FOUND")
    c = AD.Connect()
        
    # Keep this off - exposes too much
    # ld = AD._ldap

    # whoami = AD._ldap.extend.standard.who_am_i()

    cn_name = "s777777"
    dn = "cn=s777777,ou=cse,ou=students,dc=pencol,dc=local"
    container_dn = "ou=cse,ou=students,dc=pencol,dc=local"

    #current_enrollment = Canvas.GetCurrentClasses(cn_name)
    #courses = {}
    #for e in current_enrollment:
    #    courses[e['id']] = e['updated_at']

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

    #ret = AD.VerifyADSettings(False)



    last_login_time = AD.GetLastLoginTime(dn)

    refresh_all_ad_logins()

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

    #initial_run = cache.ram("startup", lambda:True, time_expire=3600)
    #cache_time = cache.ram("tmptime", lambda:time.ctime(), time_expire=30)
    
    #students = current.db(db.student_info).select()
    #student_list = []
    #for student in students:
    #    student_list.append(student)
    #    print(str(student.student_name) + " => " + str(student.student_password))
    
    #student_list = None
    
    record = db(db.media_files.id==14).select().first()
    form = SQLFORM(db["media_files"], record).process()
    
    if form.accepted:
        print("OK!!!")
        response.flash = "It Worked!"
    elif form.errors:
        print("Err: " + str(form.errors))
        response.flash = "ERR"
    else:
        print("NONE")

    #print("App: " + AppSettings.GetValue("app_name", "NO!"))
    #AppSettings.SetValue("app_name", "SMC")
    #AppSettings.SetValue("ad_service_pw", "SMC")
    #AppSettings.SetValue("app_logo", "")
    #AppSettings.SetValue("file_server_login_pass", "")
    #AppSettings.SetValue("canvas_server_password", "")
    
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
