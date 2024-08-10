# -*- coding: utf-8 -*-

import uuid
import random
from ednet.appsettings import AppSettings
from ednet.util import Util

# Help shut up pylance warnings
if 1==2: from ..common import *


# Do we need to do initial init? (e.g. creating indexes.....)
db_init_needed = cache.ram('db_init_needed', lambda: True, time_expire=3600)


db.define_table("quota_sizes",
                Field("int_size", "bigint"),
                Field("display_size"),
                Field("sort_order", "integer")
                )

# db(db.quota_sizes).delete()

if db_init_needed and db(db.quota_sizes).count() < 1:
        # Add a row
        db.quota_sizes.insert(int_size='0',
                              display_size='0 Meg',
                              sort_order="1")
        db.quota_sizes.insert(int_size='1048576',
                              display_size='1 Meg',
                              sort_order="2")
        db.quota_sizes.insert(int_size='5242880',
                              display_size='5 Meg',
                              sort_order="3")
        db.quota_sizes.insert(int_size='10485760',
                              display_size='10 Meg',
                              sort_order="4")
        db.quota_sizes.insert(int_size='31457280',
                              display_size='30 Meg',
                              sort_order="5")
        db.quota_sizes.insert(int_size='52428800',
                              display_size='50 Meg',
                              sort_order="6")
        db.quota_sizes.insert(int_size='78643200',
                              display_size='75 Meg',
                              sort_order="7")
        db.quota_sizes.insert(int_size='104857600',
                              display_size='100 Meg',
                              sort_order="8")
        db.quota_sizes.insert(int_size='314572800',
                              display_size='300 Meg',
                              sort_order="9")
        db.quota_sizes.insert(int_size='524288000',
                              display_size='500 Meg',
                              sort_order="10")
        db.quota_sizes.insert(int_size='786432000',
                              display_size='750 Meg',
                              sort_order="11")
        db.quota_sizes.insert(int_size='1048576000',
                              display_size='1 Gig',
                              sort_order="12")
        db.quota_sizes.insert(int_size='5242880000',
                              display_size='5 Gig',
                              sort_order="13")
        db.quota_sizes.insert(int_size='10485760000',
                              display_size='10 Gig',
                              sort_order="14")
        db.quota_sizes.insert(int_size='31457280000',
                              display_size='30 Gig',
                              sort_order="15")
        db.quota_sizes.insert(int_size='52428800000',
                              display_size='50 Gig',
                              sort_order="16")
        db.quota_sizes.insert(int_size='104857600000',
                              display_size='100 Gig',
                              sort_order="17")
        db.quota_sizes.insert(int_size='314572800000',
                              display_size='300 Gig',
                              sort_order="18")
        db.quota_sizes.insert(int_size='524288000000',
                              display_size='500 Gig',
                              sort_order="19")
        db.quota_sizes.insert(int_size='786432000000',
                              display_size='750 Gig',
                              sort_order="20")
        db.quota_sizes.insert(int_size='1048576000000',
                              display_size='1 TB',
                              sort_order="21")
        db.quota_sizes.insert(int_size='5242880000000',
                              display_size='5 TB',
                              sort_order="22")
        db.quota_sizes.insert(int_size='10485760000000',
                              display_size='10 TB',
                              sort_order="23")
        db.quota_sizes.insert(int_size='31457280000000',
                              display_size='30 TB',
                              sort_order="24")
        db.quota_sizes.insert(int_size='52428800000000',
                              display_size='50 TB',
                              sort_order="25")
        db.quota_sizes.insert(int_size='104857600000000',
                              display_size='100 TB',
                              sort_order="26")
        db.quota_sizes.insert(int_size='314572800000000',
                              display_size='300 TB',
                              sort_order="27")
        db.quota_sizes.insert(int_size='524288000000000',
                              display_size='500 TB',
                              sort_order="28")
        db.quota_sizes.insert(int_size='786432000000000',
                              display_size='750 TB',
                              sort_order="29")
        db.quota_sizes.insert(int_size='1048576000000000',
                              display_size='1 PB',
                              sort_order="30")

db.define_table("zpool_datasets",
                Field("name"),
                )

if db_init_needed and db(db.zpool_datasets).count() < 1:
    db.zpool_datasets.insert(name="")

db.define_table("zpool_sync",
                Field("name"),
                )

if db_init_needed and db(db.zpool_sync).count() < 1:
    db.zpool_sync.insert(name="disabled")
    db.zpool_sync.insert(name="standard")
    db.zpool_sync.insert(name="always")


db.define_table("my_app_settings",
                Field("app_name", default="SMC"),
                Field("app_description",
                      default="Student Management Console - Import/Enrollment for Active Directory and Canvas"),
                # NOTE - keep length at 30 - full length lets it add a = to the filename which download then doesn't like
                Field("app_logo", "upload", length=30, autodelete=True),
                
                Field("ad_import_enabled", "boolean", default="False"),
                Field("file_server_import_enabled", "boolean", default="False"),
                Field("ad_service_user", default="Administrator"),
                Field("ad_service_password", "password", default=""),
                Field("ad_server_protocol", default="LDAPS://",
                      requires=IS_IN_SET(["LDAPS://", "LDAP://", "WinNT://"], zero=None)),  # LDAP:// LDAPS:// WinNT://
                Field("ad_server_address", default="AD.CORRECTIONSED.COM"),
                Field("file_server_address", default="FILES.CORRECTIONSED.COM"),
                Field("file_server_quota_drive", default="",
                      requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:",
                                          "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:",
                                          "Z:"], zero=None)),
                Field("file_server_login_user", default="Administrator"),
                Field("file_server_login_pass", "password", default=""),
                Field("student_id_pattern", default="s<user_id>"),
                Field("student_password_pattern", default="Sid<user_id>!"),
                Field("student_email_pattern", default="<user_name>@correctionsed.com"),
                Field("ad_student_cn", default="OU=<program>,OU=Students,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_student_group_cn", default="OU=StudentGroups,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_student_home_directory", default="\\\\files\\students\\%username%"),
                Field("ad_student_home_drive", default="",
                      requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:",
                                          "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:",
                                          "Z:"], zero=None)),
                Field("ad_student_profile_directory", default=""),
                Field("ad_student_login_script_path", default=""),
                Field("ad_student_home_directory_quota", "bigint", default="52428800",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s',
                                        zero=None, orderby="sort_order")),
                Field("faculty_id_pattern", default="<user_id>"),
                Field("faculty_password_pattern", default="Fid<user_id>#"),
                Field("faculty_email_pattern", default="<user_name>@correctionsed.com"),
                Field("ad_faculty_cn", default="OU=<program>,OU=Faculty,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_faculty_group_cn", default="OU=FacultyGroups,DC=ad,DC=correctionsed,DC=com"),
                Field("ad_faculty_home_directory", default="\\\\files\\faculty\\%username%"),
                Field("ad_faculty_home_drive", default="",
                      requires=IS_IN_SET(["", "C:", "D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:",
                                          "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:",
                                          "Z:"], zero=None)),
                Field("ad_faculty_profile_directory", default=""),
                Field("ad_faculty_login_script_path", default=""),
                Field("ad_faculty_home_directory_quota", "bigint", default="52428800000",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None,
                                        orderby="sort_order")),
                Field("canvas_import_enabled", "boolean", default="False"),
                Field("canvas_access_token", 'string', default=""),
                Field("canvas_secret", 'string', default="<ENV>"),
                Field("canvas_database_password", 'password', default='<ENV>'),
                Field("canvas_database_server_url", default='postgresql'),
                Field("canvas_server_url", default="https://canvas.ed"),
                Field("canvas_student_quota", "bigint", default="1048576",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s',
                                        zero=None, orderby="sort_order")),
                Field("canvas_faculty_quota", "bigint", default="1048576",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s',
                                        zero=None, orderby="sort_order")),
                Field("canvas_auto_create_courses", 'boolean', default=True),
                auth.signature,
                Field("zpool_enabled", "boolean", default="False"),
                Field("zpool_login_user", default="root"),
                Field("zpool_login_password", "password", default=""),
                Field("zpool_source_dataset", "string", default="",
                      requires=IS_IN_DB(db, db.zpool_datasets.name, zero=None, orderby="name")),
                Field("zpool_dest_dataset", "string", default="",
                      requires=IS_IN_DB(db, db.zpool_datasets.name, zero=None, orderby="name")),
                Field("zpool_sync_setting", "string", default="standard",
                      requires=IS_IN_DB(db, db.zpool_sync.name, orderby="name")),
                Field("zpool_server_address", default=""),
                Field("laptop_admin_user", default="huskers"),
                Field("laptop_admin_password", "password", default="", required=True),
                Field("canvas_integration_enabled", "boolean", default="False"),
                Field("disable_student_self_change_password", "boolean", default="False"),
                Field("disable_faculty_self_change_password", "boolean", default="False"),
                Field("disable_media_auto_play", "boolean", default="True"),
                Field("laptop_network_type", "string", default="Standalone", requires=IS_IN_SET(["Standalone", "Domain Member"])),
                Field("laptop_domain_name", "string", default="SBCTC.local", required=True),
                Field("laptop_domain_ou", "string", default="laptopOU.SBCTC.local", required=True),
                Field("laptop_admin_account", "string", default="huskers", required=True),
                Field("laptop_time_servers", "list:string", default=["time.windows.com"], required=True),
                Field("laptop_approved_nics", "list:string", default=[], required=True),



                )
# force defaults for new fields to prevent nulls


# Enable encryption
db.my_app_settings.ad_service_password.filter_in = lambda value: Util.encrypt(value)
db.my_app_settings.ad_service_password.filter_out = lambda value: Util.decrypt(value)
db.my_app_settings.file_server_login_pass.filter_in = lambda value: Util.encrypt(value)
db.my_app_settings.file_server_login_pass.filter_out = lambda value: Util.decrypt(value)
db.my_app_settings.zpool_login_password.filter_in = lambda value: Util.encrypt(value)
db.my_app_settings.zpool_login_password.filter_out = lambda value: Util.decrypt(value)
db.my_app_settings.laptop_admin_password.filter_in = lambda value: Util.encrypt(value)
db.my_app_settings.laptop_admin_password.filter_out = lambda value: Util.decrypt(value)
db.my_app_settings.canvas_database_password.filter_in = lambda value: Util.encrypt(value)
db.my_app_settings.canvas_database_password.filter_out = lambda value: Util.decrypt(value)


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
                Field("student_ad_quota", "bigint", default="52428800",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size,
                                        '%(display_size)s', zero=None, orderby="sort_order")),
                Field("student_canvas_quota", "bigint", default="1048576",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s',
                                        zero=None, orderby="sort_order")),
                auth.signature,
                Field("ad_last_login", type="datetime", default=None),
                Field("canvas_auth_token", default="")
                )

# Enable encryption
db.student_info.student_password.filter_in = lambda value : Util.encrypt(value)
db.student_info.student_password.filter_out = lambda value : Util.decrypt(value)

# Indexes
if db_init_needed:
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

# Enable encryption
db.student_import_queue.student_password.filter_in = lambda value: Util.encrypt(value)
db.student_import_queue.student_password.filter_out = lambda value: Util.decrypt(value)

db.define_table("student_ad_import_status",
                Field("user_id")
                )

db.define_table("student_canvas_import_status",
                Field("user_id")
                )

db.define_table("student_excel_uploads",
                Field("excel_file", 'upload', length=240, autodelete=True, requires=IS_NOT_EMPTY(error_message="Please upload an excel file!")),
                auth.signature
                )

db.define_table("student_ad_import_queue",
                Field("student_import_queue", "reference student_import_queue")
                )

db.define_table("student_canvas_import_queue",
                Field("student_import_queue", "reference student_import_queue")
                )

# Faculty Tables
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
                Field("faculty_ad_quota", "bigint", default="52428800000",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None,
                                        orderby="sort_order")),
                Field("faculty_canvas_quota", "bigint", default="1048576",
                      requires=IS_IN_DB(db, db.quota_sizes.int_size, '%(display_size)s', zero=None,
                                        orderby="sort_order")),
                auth.signature,
                Field("ad_last_login", type="datetime", default=None),
                Field("canvas_auth_token", default="")
                )

# Enable encryption
db.faculty_info.faculty_password.filter_in = lambda value : Util.encrypt(value)
db.faculty_info.faculty_password.filter_out = lambda value : Util.decrypt(value)

# Indexes
if db_init_needed:
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

# Enable encryption
db.faculty_import_queue.faculty_password.filter_in = lambda value: Util.encrypt(value)
db.faculty_import_queue.faculty_password.filter_out = lambda value: Util.decrypt(value)

db.define_table("faculty_ad_import_status",
                Field("user_id")
                )

db.define_table("faculty_canvas_import_status",
                Field("user_id")
                )

db.define_table("faculty_excel_uploads",
                Field("excel_file", 'upload', length=240, autodelete=True, requires=IS_NOT_EMPTY(error_message="Please upload an excel file!")),
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
                Field('media_file', 'upload', length=240, autodelete=True, uploadseparate=True,
                      requires=IS_NOT_EMPTY()),
                Field('width', 'integer', default=0),
                Field('height', 'integer', default=0),
                Field('quality', 'string', default='normal', requires=IS_IN_SET(['normal', 'low', 'high'])),
                Field('status', 'string', default='queued',
                      requires=IS_IN_SET(['queued', 'processing', 'done'])),
                auth.signature,
                Field('youtube_url', 'string', default='')
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
                Field('youtube_url', 'string', default=''),
                Field('needs_downloading', 'boolean', default=False),
                auth.signature,
                Field('item_version', 'bigint', default=0),
                Field('download_failures', 'integer', default=0),
                Field('download_log', 'text', default=''),
                Field('current_download', 'boolean', default=False),
                Field('needs_caption_downloading', 'boolean', default=False),
                Field('last_download_attempt', 'datetime', default=None),
                Field('has_captions', 'boolean', default=False),
                Field('youtube_url_cleaned', 'boolean', default=False),
                )

# Indexes
if db_init_needed:
      db.executesql('CREATE INDEX IF NOT EXISTS media_guid_idx ON media_files (media_guid);')
      db.executesql('CREATE INDEX IF NOT EXISTS media_search_idx ON media_files (title, description, category, tags, youtube_url, needs_downloading, item_version);')
      db.executesql('CREATE INDEX IF NOT EXISTS media_download_idx ON media_files (last_download_attempt, current_download, download_failures, needs_caption_downloading);')
      db.executesql('CREATE INDEX IF NOT EXISTS media_url_cleaned_idx ON media_files (has_captions, youtube_url_cleaned);')


db.define_table('document_import_queue',
                Field('document_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string'),
                Field('original_file_name', 'string'),
                Field('media_type', 'string', default='document', requires=IS_IN_SET(['document'])),
                Field('category', 'string'),
                Field('tags', 'list:string'),
                Field('document_file', 'upload', length=240, autodelete=True, uploadseparate=True,
                      requires=IS_NOT_EMPTY()),
                Field('status', 'string', default='queued',
                      requires=IS_IN_SET(['queued', 'processing', 'done'])),
                auth.signature,
                Field('source_url', 'string', default='')
                )

db.define_table('document_files',
                Field('document_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string'),
                Field('original_file_name', 'string'),
                Field('media_type', 'string', default='document', requires=IS_IN_SET(['document'])),
                Field('category', 'string'),
                Field('tags', 'list:string'),
                Field('views', 'integer', default=0),
                Field('google_url', 'string', default=''),
                auth.signature,
                Field('source_url', 'string', default=''),
                Field('link_to_pdf', 'string', default=''),
                Field('item_version', 'bigint', default=0),
                Field('width', 'string', default='0'),
                Field('height', 'string', default='0'),
                )

# Indexes
if db_init_needed:
      db.executesql('CREATE INDEX IF NOT EXISTS document_guid_idx ON document_files (document_guid);')


db.define_table('playlist',
                Field('playlist_guid', 'string', default=str(uuid.uuid4()).replace('-', '')),
                Field('title', 'string', requires=IS_NOT_EMPTY()),
                auth.signature,
                rname="playlists_1"
                )

db.define_table('playlist_items',
                Field('playlist', 'reference playlist'),
                Field('media_file', 'reference media_files'),
                Field('playlist_order', 'integer', default=0),
                auth.signature
                )

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

if db_init_needed:
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

if db_init_needed:
      db.executesql('CREATE INDEX IF NOT EXISTS source_id_idx ON wamap_qimages (source_id);')

db.define_table('wamap_pdfs',
                Field('source_url', 'string'),
                Field('new_url', 'string'),
                Field('downloaded', 'boolean', default=False),
                Field('media_guid', 'string'),
                auth.signature
                )
if db_init_needed:
      db.executesql('CREATE INDEX IF NOT EXISTS media_guid_idx ON wamap_pdfs (media_guid);')
      db.executesql('CREATE INDEX IF NOT EXISTS source_url_idx ON wamap_pdfs (source_url);')
      db.executesql('CREATE INDEX IF NOT EXISTS downloaded_idx ON wamap_pdfs (downloaded);')


# Tables for inmate laptop firewall rules
db_laptops.define_table('ope_laptop_firewall_rules',
                Field('rule_name', 'string', requires=IS_NOT_EMPTY()),
                Field('direction', 'string', default='in', requires=IS_IN_SET(['in', 'out'])),
                Field('fw_action', 'string', default='allow', requires=IS_IN_SET(['allow', 'block', 'bypass'])),
                Field('program', 'string', default='', label="Program (path to exe or blank)"),
                Field('service', 'string', default='', label="Service (short name or blank)"),
                Field('description', 'string', default=''),
                Field('fw_enable', 'string', default='yes', requires=IS_IN_SET(['yes', 'no']),
                      label="Enable (yes or no)"),
                Field('profile', 'string', default='any', requires=IS_IN_SET(['any', 'public', 'private', 'domain'])),
                Field('localip', 'string', default=''),
                Field('remoteip', 'string', default=''),
                Field('localport', 'string', default='any'),  # , requires=[IS_IN_SET(['any', 'rpc', 'rpc-epmap', 'iphttps', 'teredo'], IS_INT_IN_RANGE(1, 65535))], label="Local Port (port number or any, rpc, rpc-epmap, iphttps, toredo)"),
                Field('remoteport', 'string', default='any'),  # , requires=[IS_IN_SET(['any'], IS_INT_IN_RANGE(1, 65535))], label="Remote Port (port number or any, rpc, rpc-epmap, iphttps, toredo)"),
                Field('protocol', 'string', default='tcp'),  # , requires=[IS_IN_SET(['any', 'icmpv4', 'icmpv6', 'tcp', 'udp'], IS_INT_IN_RANGE(1, 65535))], label="Protocol (protocl number or any, icmpv4, icmpv6, tcp, udp)"),
                Field('interfacetype', 'string', default='any', requires=IS_IN_SET(['any', 'wireless', 'lan', 'ras'])),
                Field('rmtcomputergrp', 'string', default='',
                      label="Rmtcomputergrp (SDDLString - see netsh advfirewall for more info)"),
                Field('rmtusrgrp', 'string', default='', label="Rmtusrgrp (same as Rmtcomputergrp)"),
                Field('edge', 'string', default='no', requires=IS_IN_SET(['yes', 'deferapp', 'deferuser', 'no'])),
                Field('fw_security', 'string', default='notrequired',
                      requires=IS_IN_SET(['authenticate', 'authenc', 'authdynenc', 'authnoencap', 'notrequired']),
                      label="Security (ISec options - default notrequired)"),
                Field('can_modify', 'boolean', default=True, writable=False, readable=False),
                )


# Tables for laptop logs and information
db_laptops.define_table("ope_laptops",
      Field('auth_key', 'string', default=str(uuid.uuid4()).replace('-', '')),
      Field('bios_serial_number', 'string', requires=IS_NOT_EMPTY()),
      Field('boot_disk_serial_number', 'string', default=''),
      Field('state_tracking_number', 'string', default=""),
      Field('current_student', 'string', default=""),
      Field('admin_user', 'string', default=""),
      Field('credentialed_by_user', 'string', default=""),
      Field('last_sync_date', 'datetime', default=None),
      Field('bios_name', 'string', default=""),
      Field('bios_version', 'string', default=""),
      Field('bios_manufacturer', 'string', default=""),
      Field('admin_password_status', 'string', default=""),
      Field('archived', 'boolean', default=False),
      Field('extra_info', 'json'),
      Field('laptop_version', 'string', default='')
)

db_laptops.define_table("ope_laptop_logs",
      Field("parent_id", "reference ope_laptops"),
      Field("push_date", 'datetime'),
      Field("log_type", 'string', requires=IS_IN_SET(
            ["machine_info", "event_logs", "file_changes"]
            )),
      #Field(""),
      Field('log_name', 'string', required=True),
      Field('extra_info', 'json'),
)

db_laptops.define_table("ope_laptop_screen_shots",
      Field("parent_id", "reference ope_laptops"),
      Field("file_date", 'datetime'),
      Field("push_date", 'datetime'),
      Field("credentialed_user", 'string', default=""),
      Field("archived", 'boolean', default=False),
      Field("flagged", 'boolean', default=False),
      Field('img_file', 'upload', length=240, autodelete=True, uploadseparate=True,
            requires=IS_NOT_EMPTY(error_message="Please attach a screen shot file!")),
)

db.define_table("youtube_proxy_list",
      Field("protocol", "string", default="https"),
      Field("proxy_url", "string", default=""),
      Field("enabled", "boolean", default=True),
      Field("last_429_error_on", "datetime"),
      auth.signature,
      Field("last_error_on", "datetime"),
      Field("last_request_on", "datetime"),
)


# LTI Tables

# A list of LTI connections registered here (e.g. 1 for each canvas integration instance)
db_lti.define_table("lti_registrations",
      Field("name", 'string', required=True, default="SMC LTI Integration"),
      Field("description", 'string', default='SMC LTI Integration for Learning Management Systems.'),
      Field("issuer", 'string', default='https://canvas.ed', required=True),
      Field("client_id", 'string', default='SMCIntegration_' + str(random.randint(0,200))),
      Field("deployment_ids", 'list:string', default=[int(time.time())]),
      Field("key_set_url", 'string', default=URL(a='smc', c='lti', f='jwks', host=True, scheme=True)),
      Field("key_set", 'string', default=''),
      Field("auth_token_url", 'string'),
      Field("auth_login_url", 'string', default=URL(a='smc', c='lti', f='oidc_login', host=True, scheme=True)),
      Field("public_key", 'text'),
      Field("private_key", 'text'),
      Field("jwks_str", 'text'),
      Field("is_default", 'boolean', default=False)
)

db_lti.define_table("ope_quizzes",
      Field("imported_canvas_quiz_id", 'integer', default=0, required=True),
      Field("lms_parent_course", "string", default=""),
      Field("title", 'string', requires=IS_NOT_EMPTY()),
      Field("description", 'text', default=""),
      Field("quiz_type", 'string', default="assignment", requires=IS_IN_SET(["assignment", "practice_quiz", "graded_survey", "survey"])),
      Field("assignment_group_id", 'integer', default=0),
      Field("time_limit_enabled", 'boolean', default=False),
      Field("time_limit", 'integer', default=0),                        # in minutes
      Field("shuffle_answers", 'boolean', default=True),
      Field("never_hide_results", 'boolean', default=True),
      Field("hide_results_only_after_last", 'boolean', default=False),
      Field("one_time_results", 'boolean', default=False),
      Field("hide_results", 'string', default="always", requires=IS_IN_SET(["always", "until_after_last_attempt", "null"])), # How does this equate to an input?
      Field("show_correct_answers", 'boolean', default=False),
      Field("show_correct_answers_last_attempt", 'boolean', default=False),
      Field("show_correct_answers_at", 'datetime'),
      Field("hide_correct_answers_at", 'datetime'),
      Field("scoring_policy", 'string', default="keep_highest", requires=IS_IN_SET(["keep_highest", "keep_latest", "average"])),
      Field("allow_multiple_attempts", 'boolean', default=False),
      Field("allowed_attempts", 'integer', default=1, requires=IS_INT_IN_RANGE(1, 99)),
      Field("one_question_at_a_time", 'boolean', default=True),
      Field("question_count", 'integer', default=0),
      Field("cant_go_back", 'boolean', default=True),
      Field("enable_quiz_access_code", 'boolean', default=False),
      Field("access_code", 'string', default=""),
      Field("enable_quiz_ip_filter", 'boolean', default=False),
      Field("ip_filter", 'string', default=""),
      Field("due_at", 'datetime'),
      Field("lock_at", 'datetime'),
      Field("unlock_at", 'datetime'),
      Field("published", 'boolean', default=False),
      Field("unpublishable", 'boolean', default=False),
      Field("version_number", 'integer', default=1),
      Field("anonymous_submissions", 'boolean', default=False),   # For survey types where you want data anonymzied
      Field("available_on_offline_laptop", 'boolean', default=False),
      Field("enc_key", 'string', default=str(uuid.uuid4()).replace("-", "")),  # Used by the laptop to encrypt the quiz information
      Field("quiz_position", 'integer', default=0),
      Field("points_possible", 'double', default=0),

)

db_lti.define_table("ope_question_banks",
      Field("lms_parent_course", "string", default=""),
      Field("bank_title", "string", required=True),
      Field("bank_description", "string", default=""),
      Field("question_bank_position", "integer", default=0),
)

db_lti.define_table("ope_question_groups",
      Field("parent_quiz", "reference ope_quizzes"),
      Field("group_title", "string", required=True),
      Field("pick_number_questions", "integer", required=True, default=0),
      Field("points_per_question", "double", default=0),
      Field("question_groups_position", "integer", default=0),
)

db_lti.define_table("ope_quiz_questions",
      Field("parent_quiz", "reference ope_quizzes"),
      Field("parent_question_group", "integer", default=0),
      Field("parent_question_bank", "integer", default=0),
      Field("question_position", "integer", default=0),
      Field("question_name", "string", required=True),
      Field("question_type", "string", requires=IS_IN_SET([
            "true_false_question", "calculated_question", "essay_question", "file_upload_question",
            "fill_in_multiple_blanks_question", "matching_question", "multiple_answers_question",
            "multiple_choice_question", "multiple_dropdowns_question", "numerical_question",
            "short_answer_question", "text_only_question",
            ])),
      Field("question_text", "string", default=""),
      Field("points_possible", "decimal(4,2)", default=1),
      Field("correct_comments", "string", default=""),
      Field("incorrect_comments", "string", default=""),
      Field("neutral_comments", "string", default=""),
      Field("text_after_answers", "string", default=""),
)

db_lti.define_table("ope_quiz_answers",
      Field("ope_quiz_question", "reference ope_quiz_questions"),
      Field("is_correct_answer", 'boolean', default=False),
      Field("answer_text", "string", default=""),
      Field("answer_weight", "integer", default=100),
      Field("answer_comments", "string", default=""),
      Field("text_after_answers", "string", default=""),
      Field("answer_match_left", "string", default=""),
      Field("answer_match_right", "string", default=""),
      Field("matching_answer_incorrect_matches", "list:string", default=[]),
      Field("numerical_answer_type", "string", default="exact_answer", requires=IS_IN_SET(["exact_answer", "range_answer", "precision_answer"])),
      Field("exact", "string", default=""),
      Field("margin", "string", default="0"),
      Field("approximate", "string", default="0"),
      Field("precision_value", "string", default=""),
      Field("range_start", "string", default=""),
      Field("range_end", "string", default=""),
      Field("fill_in_the_blank_answer", "string", default=""),
)


# Indexes - Add indexes for system tables
if db_init_needed:
      db.executesql('CREATE INDEX IF NOT EXISTS auth_membership_idx ON auth_membership (id, user_id, group_id);')
      db.executesql('CREATE INDEX IF NOT EXISTS auth_group_idx ON auth_group (id, role);')
      db.executesql('CREATE INDEX IF NOT EXISTS auth_user_idx ON auth_user (id, username, email, first_name, last_name);')


# Adjust the app logo if it is set
app_logo = AppSettings.GetValue('app_logo', '<none>')
if app_logo != "<none>":
    app_logo = IMG(_src=URL('download', app_logo), _alt="SMC - App Logo", _class="brand",_style="height: 50px;")
else:
    app_logo = IMG(_src=URL('static','images/sbctc_logo.png'), _alt="SMC - App Logo", _class="brand",_style="height: 50px;")

response.logo = app_logo
response.title = AppSettings.GetValue('app_name', request.application.replace('_',' ').title())
response.subtitle = AppSettings.GetValue('app_description',
                                    'OPE Support tools for secure Canvas installations')



### NOTE - db_init_needed is turned off in x_fixtures
