# coding: utf8


## Make sure that these entries are present in the database
# Groups
if db(db.auth_group.id > 0).count() == 0:
   db.auth_group.insert(role='Administrators', description='Users with administrative privileges')
   db.auth_group.insert(role='Import', description='Users with import privileges')
   db.auth_group.insert(role='Students', description='Users with student privileges')
   db.auth_group.insert(role='Faculty', description='Faculty members')

g = db(db.auth_group.role=='Media Upload').select().first()
if (g == None):
    db.auth_group.insert(role='Media Upload', description='Users with permission to upload media files')

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
    new_admin = True

# Ensure admin is in administrators group
if (new_admin):
    admin_group_id = auth.id_group("Administrators")
    row = db(db.auth_user.username == "admin").select().first()
    admin_id = row["id"]
    auth.add_membership(group_id=admin_group_id, user_id=admin_id)
new_admin = False
