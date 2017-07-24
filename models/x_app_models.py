# coding: utf8

import uuid

from ednet.appsettings import AppSettings
from ednet.util import Util

db.define_table("quota_sizes",
                Field("int_size", "bigint"),
                Field("display_size"),
                Field("sort_order", "integer")
                )

#db(db.quota_sizes).delete()
if (db(db.quota_sizes).count() < 1):
        # Add a row
        db.quota_sizes.insert(int_size= '0',
                              display_size= '0 Meg',
                              sort_order="1")
        
        db.quota_sizes.insert(int_size= '1048576',
                              display_size= '1 Meg',
                              sort_order="2")
        
        db.quota_sizes.insert(int_size= '5242880',
                              display_size= '5 Meg',
                              sort_order="3")
        
        db.quota_sizes.insert(int_size= '10485760',
                              display_size= '10 Meg',
                              sort_order="4")
        
        db.quota_sizes.insert(int_size= '31457280',
                              display_size= '30 Meg',
                              sort_order="5")
        
        db.quota_sizes.insert(int_size= '52428800',
                              display_size= '50 Meg',
                              sort_order="6")
        
        db.quota_sizes.insert(int_size= '78643200',
                              display_size= '75 Meg',
                              sort_order="7")
        
        db.quota_sizes.insert(int_size= '104857600',
                              display_size= '100 Meg',
                              sort_order="8")
        
        db.quota_sizes.insert(int_size= '314572800',
                              display_size= '300 Meg',
                              sort_order="9")
        
        db.quota_sizes.insert(int_size= '524288000',
                              display_size= '500 Meg',
                              sort_order="10")
        
        db.quota_sizes.insert(int_size= '786432000',
                              display_size= '750 Meg',
                              sort_order="11")
        
        db.quota_sizes.insert(int_size= '1048576000',
                              display_size= '1 Gig',
                              sort_order="12")
        
        db.quota_sizes.insert(int_size= '5242880000',
                              display_size= '5 Gig',
                              sort_order="13")
        
        db.quota_sizes.insert(int_size= '10485760000',
                              display_size= '10 Gig',
                              sort_order="14")
        
        db.quota_sizes.insert(int_size= '31457280000',
                              display_size= '30 Gig',
                              sort_order="15")
        
        db.quota_sizes.insert(int_size= '52428800000',
                              display_size= '50 Gig',
                              sort_order="16")
        
        db.quota_sizes.insert(int_size= '104857600000',
                              display_size= '100 Gig',
                              sort_order="17")
        
        db.quota_sizes.insert(int_size= '314572800000',
                              display_size= '300 Gig',
                              sort_order="18")
        
        db.quota_sizes.insert(int_size= '524288000000',
                              display_size= '500 Gig',
                              sort_order="19")
        
        db.quota_sizes.insert(int_size= '786432000000',
                              display_size= '750 Gig',
                              sort_order="20")
        
        db.quota_sizes.insert(int_size= '1048576000000',
                              display_size= '1 TB',
                              sort_order="21")
        
        db.quota_sizes.insert(int_size= '5242880000000',
                              display_size= '5 TB',
                              sort_order="22")
        
        db.quota_sizes.insert(int_size= '10485760000000',
                              display_size= '10 TB',
                              sort_order="23")
        
        db.quota_sizes.insert(int_size= '31457280000000',
                              display_size= '30 TB',
                              sort_order="24")
        
        db.quota_sizes.insert(int_size= '52428800000000',
                              display_size= '50 TB',
                              sort_order="25")
        
        db.quota_sizes.insert(int_size= '104857600000000',
                              display_size= '100 TB',
                              sort_order="26")
        
        db.quota_sizes.insert(int_size= '314572800000000',
                              display_size= '300 TB',
                              sort_order="27")
        
        db.quota_sizes.insert(int_size= '524288000000000',
                              display_size= '500 TB',
                              sort_order="28")
        
        db.quota_sizes.insert(int_size= '786432000000000',
                              display_size= '750 TB',
                              sort_order="29")
        
        db.quota_sizes.insert(int_size= '1048576000000000',
                              display_size= '1 PB',
                              sort_order="30")


db.define_table("zpool_datasets",
                Field("name"),
                )
if (db(db.zpool_datasets).count() < 1):
    db.zpool_datasets.insert(name="")

db.define_table("zpool_sync",
                Field("name"),
                )
if (db(db.zpool_sync).count() < 1):
    db.zpool_sync.insert(name="disabled")
    db.zpool_sync.insert(name="standard")
    db.zpool_sync.insert(name="always")

db.define_table("my_app_settings",
                Field("app_name", default="SMC"),
                Field("app_description", default="Student Management Console - Import/Enrollment for Active Directory and Canvas"),
                Field("app_logo", "upload", autodelete=True),
                
                Field("ad_import_enabled", "boolean", default="False"),
                Field("file_server_import_enabled", "boolean", default="False"),
                Field("ad_service_user", default="Administrator"),
                Field("ad_service_password", "password", default="super secret password"),
                Field("ad_server_protocol", default="LDAPS://", requires=IS_IN_SET(["LDAPS://", "LDAP://", "WinNT://"], zero=None)), # LDAP:// LDAPS:// WinNT://
                Field("ad_server_address", default="AD.CORRECTIONSED.COM"),
                Field("file_server_address", default="FILES.CORRECTIONSED.COM"),
                Field("file_server_quota_drive", default="", requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:", "Z:" ], zero=None)),
                Field("file_server_login_user", default="Administrator"),
                Field("file_server_login_pass", "password", default="super secret password"),
                Field("student_id_pattern", default="s<user_id>"),
                Field("student_password_pattern", default="SID<user_id>!"),
                Field("student_email_pattern", default="s<user_id>@correctionsed.com"),
                Field("ad_student_cn", default="OU=Students,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_student_group_cn", default="OU=StudentGroups,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_student_home_directory", default="\\\\files\\students\\%username%"),
                Field("ad_student_home_drive", default="", requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:", "Z:" ], zero=None)),
                Field("ad_student_profile_directory", default=""),
                Field("ad_student_login_script_path", default=""),
                Field("ad_student_home_directory_quota", "bigint", default="0", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("faculty_id_pattern", default="f<user_id>"),
                Field("faculty_password_pattern", default="FID<user_id>#"),
                Field("faculty_email_pattern", default="<user_name>@correctionsed.com"),
                Field("ad_faculty_cn", default="OU=Faculty,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_faculty_group_cn", default="OU=FacultyGroups,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_faculty_home_directory", default="\\\\files\\faculty\\%username%"),
                Field("ad_faculty_home_drive", default="", requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:", "Z:" ], zero=None)),
                Field("ad_faculty_profile_directory", default=""),
                Field("ad_faculty_login_script_path", default=""),
                Field("ad_faculty_home_directory_quota", "bigint", default="0", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("canvas_import_enabled", "boolean", default="False"),
                Field("canvas_access_token", 'string', default=""),
                Field("canvas_secret", 'string', default="<ENV>"),
                Field("canvas_server_url", default="https://canvas.ed"),
                Field("canvas_student_quota", "bigint", default="1048576", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("canvas_faculty_quota", "bigint", default="1048576", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("canvas_auto_create_courses", 'boolean', default=True),
                auth.signature,
                Field("zpool_enabled", "boolean", default="False"),
                Field("zpool_login_user", default="root"),
                Field("zpool_login_password", "password", default=""),
                Field("zpool_source_dataset", "string", default="", requires=IS_IN_DB(db, db.zpool_datasets.name, zero=None, orderby="name")),
                Field("zpool_dest_dataset", "string", default="", requires=IS_IN_DB(db, db.zpool_datasets.name, zero=None, orderby="name")),
                Field("zpool_sync_setting", "string", default="standard", requires=IS_IN_DB(db, db.zpool_sync.name, orderby="name")),
                Field("zpool_server_address", default=""),
                )

## Enable encryption
db.my_app_settings.ad_service_password.filter_in = lambda value : Util.encrypt(value)
db.my_app_settings.ad_service_password.filter_out = lambda value : Util.decrypt(value)
db.my_app_settings.file_server_login_pass.filter_in = lambda value : Util.encrypt(value)
db.my_app_settings.file_server_login_pass.filter_out = lambda value : Util.decrypt(value)
db.my_app_settings.zpool_login_password.filter_in = lambda value : Util.encrypt(value)
db.my_app_settings.zpool_login_password.filter_out = lambda value : Util.decrypt(value)


db.define_table("student_info",
                Field("account_id", "reference auth_user"),
                Field("user_id"),
                Field("student_name"),
                Field("student_password", "password"),
                Field("import_classes"),
                Field("program", "string", default=""),
                Field("additional_fields", "text"),
                Field("sheet_name"),
                Field("student_guid"),
                Field("account_enabled", "boolean", default="True"),
                Field("account_added_on"),
                Field("account_updated_on"),
                Field("student_ad_quota", "bigint", default="0", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("student_canvas_quota", "bigint", default="1048576", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                auth.signature,
                Field("ad_last_login", type="datetime", default=None),
                Field("canvas_auth_token", default="")
                )

# Enable encryption
db.student_info.student_password.filter_in = lambda value : Util.encrypt(value)
db.student_info.student_password.filter_out = lambda value : Util.decrypt(value)

# Indexes
db.executesql('CREATE INDEX IF NOT EXISTS account_id_idx ON student_info (account_id);')
db.executesql('CREATE INDEX IF NOT EXISTS user_id_idx ON student_info (user_id);')

db.define_table("student_enrollment",
                Field("parent_id", "reference student_info"),
                Field("course_code", "string", requires=IS_NOT_EMPTY()),
                Field("enrolled_on", "string"),
                Field("enrollment_status", default="active", requires=IS_IN_SET(["active", "completed", "disabled"])),
                auth.signature
                )

db.define_table("student_import_queue",
                Field("user_id"),
                Field("student_name"),
                Field("student_password", "password"),
                Field("import_classes"),
                Field("program", "string", default=""),
                Field("additional_fields", "text"),
                Field("sheet_name"),
                Field("student_guid"),
                Field("account_enabled", "boolean", default="True"),
                Field("account_added_on"),
                Field("account_updated_on"),
                auth.signature
                )

## Enable encryption
db.student_import_queue.student_password.filter_in = lambda value : Util.encrypt(value)
db.student_import_queue.student_password.filter_out = lambda value : Util.decrypt(value)

db.define_table("student_ad_import_status",
                Field("user_id")
                )

db.define_table("student_canvas_import_status",
                Field("user_id")
                )

db.define_table("student_excel_uploads",
                Field("excel_file", 'upload', autodelete=True),
                auth.signature
                )

db.define_table("student_ad_import_queue",
                Field("student_import_queue", "reference student_import_queue")
                )

db.define_table("student_canvas_import_queue",
                Field("student_import_queue", "reference student_import_queue")
                )

#### Faculty Tables
db.define_table("faculty_info",
                Field("account_id", "reference auth_user"),
                Field("user_id"),
                Field("faculty_name"),
                Field("faculty_password", "password"),
                Field("import_classes"),
                Field("program", "string", default=""),
                Field("additional_fields", "text"),
                Field("sheet_name"),
                Field("faculty_guid"),
                Field("account_enabled", "boolean", default="True"),
                Field("account_added_on"),
                Field("account_updated_on"),
                Field("faculty_ad_quota", "bigint", default="0", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                Field("faculty_canvas_quota", "bigint", default="1048576", requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None, orderby="sort_order")),
                auth.signature,
                Field("ad_last_login", type="datetime", default=None),
                Field("canvas_auth_token", default="")
                )

## Enable encryption
db.faculty_info.faculty_password.filter_in = lambda value : Util.encrypt(value)
db.faculty_info.faculty_password.filter_out = lambda value : Util.decrypt(value)

## Indexes
db.executesql('CREATE INDEX IF NOT EXISTS account_id_idx ON faculty_info (account_id);')
db.executesql('CREATE INDEX IF NOT EXISTS user_id_idx ON faculty_info (user_id);')

db.define_table("faculty_enrollment",
                Field("parent_id", "reference faculty_info"),
                Field("course_code", "string", requires=IS_NOT_EMPTY()),
                Field("enrolled_on", "string"),
                Field("enrollment_status", default="active", requires=IS_IN_SET(["active", "completed", "disabled"])),
                auth.signature
                )

db.define_table("faculty_import_queue",
                Field("user_id"),
                Field("faculty_name"),
                Field("faculty_password", "password"),
                Field("import_classes"),
                Field("program", "string", default=""),
                Field("additional_fields", "text"),
                Field("sheet_name"),
                Field("faculty_guid"),
                Field("account_enabled", "boolean", default="True"),
                Field("account_added_on"),
                Field("account_updated_on"),
                auth.signature
                )

## Enable encryption
db.faculty_import_queue.faculty_password.filter_in = lambda value : Util.encrypt(value)
db.faculty_import_queue.faculty_password.filter_out = lambda value : Util.decrypt(value)

db.define_table("faculty_ad_import_status",
                Field("user_id")
                )

db.define_table("faculty_canvas_import_status",
                Field("user_id")
                )

db.define_table("faculty_excel_uploads",
                Field("excel_file",'upload', autodelete=True),
                auth.signature
                )

db.define_table("faculty_ad_import_queue",
                Field("faculty_import_queue", "reference faculty_import_queue")
                )

db.define_table("faculty_canvas_import_queue",
                Field("faculty_import_queue", "reference faculty_import_queue")
                )

# Media File Tables
db.define_table('media_file_import_queue',
                Field('media_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string'),
                Field('original_file_name', 'string'),
                Field('media_type', 'string', default='video', requires=IS_IN_SET(['video', 'song'])),
                Field('category', 'string'),
                Field('tags', 'list:string'),
                Field('media_file','upload', autodelete=True, uploadseparate=True, requires=IS_NOT_EMPTY()),
                Field('width', 'integer', default=0),
                Field('height', 'integer', default=0),
                Field('quality', 'string', default='normal', requires=IS_IN_SET(['normal', 'low', 'high'])),
                Field('status', 'string', default='queued', requires=IS_IN_SET(['queued', 'processing', 'done'])),
                auth.signature
                )

db.define_table('media_files',
                Field('media_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string'),
                Field('original_file_name', 'string'),
                Field('media_type', 'string', default='video', requires=IS_IN_SET(['video', 'song'])),
                Field('category', 'string'),
                Field('tags', 'list:string'),
                Field('width', 'integer', default=0),
                Field('height', 'integer', default=0),
                Field('quality', 'string', default='normal', requires=IS_IN_SET(['normal', 'low', 'high'])),
                Field('views', 'integer', default=0),
                auth.signature
                )

## Indexes
db.executesql('CREATE INDEX IF NOT EXISTS media_guid_idx ON media_files (media_guid);')

db.define_table('playlist',
                Field('playlist_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                auth.signature,
                rnamne="playlists.1"
                )

db.define_table('playlist_items',
                Field('playlist', 'reference playlist'),
                Field('media_file', 'reference media_files'),
                Field('playlist_order', 'integer', default=0),
                auth.signature
                )

#deprecated!
db.define_table('wamap_questionset',
                Field('wamap_id', 'integer'),
                Field('extref_field', 'string'),
                Field('media_file_id', 'reference media_files', required=False),
                Field('processed', 'boolean', default=False),
                auth.signature
                )

db.define_table('wamap_videos',
                Field('source_url', 'string'),
                Field('new_url', 'string'),
                Field('downloaded', 'boolean', default=False),
                Field('media_guid', 'string'),
                Field('old_player_id', 'integer', default=0),
                auth.signature
                )
db.executesql('CREATE INDEX IF NOT EXISTS media_guid_idx ON wamap_videos (media_guid);')
db.executesql('CREATE INDEX IF NOT EXISTS source_url_idx ON wamap_videos (source_url);')
db.executesql('CREATE INDEX IF NOT EXISTS downloaded_idx ON wamap_videos (downloaded);')

db.define_table('wamap_qimages',
                Field('source_id', 'integer', default=0),
                Field('source_qsetid', 'integer', default=0),
                Field('source_var', 'string', default=''),
                Field('source_filename', 'string', default=''),
                Field('source_alttext', 'string', default=''),
                Field('downloaded', 'boolean', default=False),
                auth.signature
                )
db.executesql('CREATE INDEX IF NOT EXISTS source_id_idx ON wamap_qimages (source_id);')

db.define_table('wamap_pdfs',
                Field('source_url', 'string'),
                Field('new_url', 'string'),
                Field('downloaded', 'boolean', default=False),
                Field('media_guid', 'string'),
                auth.signature
                )
db.executesql('CREATE INDEX IF NOT EXISTS media_guid_idx ON wamap_pdfs (media_guid);')
db.executesql('CREATE INDEX IF NOT EXISTS source_url_idx ON wamap_pdfs (source_url);')
db.executesql('CREATE INDEX IF NOT EXISTS downloaded_idx ON wamap_pdfs (downloaded);')


# Adjust the app logo if it is set
app_logo = AppSettings.GetValue('app_logo', '<none>')
if (app_logo != "<none>"):
    app_logo = IMG(_src=URL('download', app_logo), _alt="App Logo", _class="brand",_style="height: 30px;")
else:
    app_logo = IMG(_src=URL('static','images/pc_logo.png'), _alt="App Logo", _class="brand",_style="height: 30px;")

response.logo = app_logo
response.title = AppSettings.GetValue('app_name', request.application.replace('_',' ').title())
response.subtitle = AppSettings.GetValue('app_description', 'Student Management Console - Import/Enrollment for Active Directory and Canvas')
