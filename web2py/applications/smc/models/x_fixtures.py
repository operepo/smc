# coding: utf8
import os
from ednet.ad import AD

## Make sure that these entries are present in the database
# Groups
if db(db.auth_group.id > 0).count() == 0:
   db.auth_group.insert(role='Administrators', description='Users with administrative privileges')
   db.auth_group.insert(role='Import', description='Users with import privileges')
   db.auth_group.insert(role='Students', description='Users with student privileges')
   db.auth_group.insert(role='Faculty', description='Faculty members')
   db.commit()

g = db(db.auth_group.role=='Media Upload').select().first()
if (g == None):
    db.auth_group.insert(role='Media Upload', description='Users with permission to upload media files')
    db.commit()

new_admin = False
# Starting Users
if db(db.auth_user.id > 0).count() == 0:
    db.auth_user.insert(
        first_name='admin',
        last_name='admin',
        email='admin@correctionsed.com',
        username='admin',
        #password='sha512$808af3963c00c669$111d57c854f71967c7d45bad3acb6c68685bfae6392fd9bef161a65a918c4d947051ab8d2f54cd1c4fa2e068627ce98751fa6dcf7bd8c4b4492de30f2085e7fe',
        password= 'sha512$89ae76a571eccb1e$9a7bc499dcb92f1f3f142e9a1c3c65d07ab6517ab8bfb06760a68ee8ef5de41b9d89e0a4ca1080f47654df8a0f9c443d0745443384cbfba33cab9a2ecaa08d26',
    )
    db.commit()
    new_admin = True

# Ensure admin is in administrators group
if (new_admin):
    admin_group_id = auth.id_group("Administrators")
    row = db(db.auth_user.username == "admin").select().first()
    admin_id = row["id"]
    auth.add_membership(group_id=admin_group_id, user_id=admin_id)
    db.commit()
new_admin = False

#  Make sure the admin password is setup if we are in a docker container (presence of IT_PW environment variable)
startup = cache.ram('startup', lambda: True, time_expire=600)
if (startup == True):
    # Set password
    from gluon.main import save_password
    pw = ""
    if "IT_PW" in os.environ:
        pw = str(os.environ["IT_PW"]) + ""
        pw = pw.strip()
    if (pw != ""):
        # Set pw for w2p admin login (parameters_??.py file)
        save_password(pw,80)
        save_password(pw,443)
        # Set pw for smc admin login (in the database)
        db(db.auth_user.username=='admin').update( password=db.auth_user.password.validate(pw)[0] )
        db.commit()
    # Set the cache with the new value
    cache.ram('startup', lambda: False, 0)
