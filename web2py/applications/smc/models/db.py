# -*- coding: utf-8 -*-

# Track module changes - reload on change
from gluon.custom_import import track_changes
track_changes(True)

# Help shut up pylance warnings
if 1==2: from ..common import *


# Make sure the appconfig.ini file exists
import os
import shutil
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ini_path = os.path.join(app_root, "private", "appconfig.ini")
default_ini_path = os.path.join(app_root, "appconfig.ini.default")
if not os.path.isfile(ini_path):
    # Copy the default file over
    shutil.copyfile(default_ini_path, ini_path)

# Make sure there is a Redis section in the appconfig.ini file.
ensure_redis = cache.ram("ensure_redis", lambda: True, time_expire=36000)
if ensure_redis is True:
    # Read in the appconfig.ini file - see if it has the redis section
    f = open(ini_path, 'r')
    lines = f.read()
    f.close()

    if not "[redis]" in lines:
        print(f"Adding redis to appconfig.ini...")
        lines = lines + """
; Redis Configuration
[redis]
use_for_sessions    = true
host                = redis
port                = 6379
db                  = 14
"""
    if not "[pg_db]" in lines:
        print(f"Adding postgresql to appconfig.ini...")
        lines = lines + """
; Postgreql Server
[pg_db]
pg_server       = postgresql
pg_port         = 5432
pg_database     = smc
pg_user         = postgres
pg_pass         = <IT_PW>
pg_migrate      = true
"""
        f = open(ini_path, "w")
        f.write(lines)
        f.close()
    else:
        #print("Redis config is good..")
        pass

    # Reset the value so we don't do this every page view
    cache.ram("ensure_redis", lambda: False, time_expire=0)



if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# print(request.application, request.controller, request.function, request.extension, request.view, request.folder)
if request.controller == 'default' and request.function == 'index' and request.extension == 'html':
    # Skip https here
    pass
elif request.is_scheduler is True:
    pass
else:
    # All other requests need https
    request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)


lazy_tables = True
fake_migrate_all = False
fake_migrate = False
migrate = True
migrate_enabled = False

tmp = request.vars.lazy_tables
if tmp:
    if tmp.lower() == "false":
        lazy_tables = False
        migrate_enabled = True

tmp = request.vars.fake_migrate
if tmp:
    if tmp.lower() == "true":
        fake_migrate = True
        migrate = True
        migrate_enabled = True

tmp = request.vars.fix
if tmp:
    if tmp.lower() == "true" or tmp.lower() == "all":
        cache.ram("initial_run", lambda: True, time_expire=600)
        # lazy_tables = False
        # fake_migrate = True
        migrate = True
        migrate_enabled = True

# On initial run since startup (runs every time app starts, set migrate=true&lazy_tables=false
initial_run = cache.ram("initial_run", lambda: True, time_expire=36000)
if initial_run is True:  # and request.is_scheduler is not None and request.is_schedule is not True:
    # print("Startup - first run, force db migration - is scheduler / local: "
    #      + str(request.is_scheduler) + "/" + str(request.is_local))
    # Force db migrate on first run
    lazy_tables = False
    migrate = True
    migrate_enabled = True
    fake_migrate = False
    fake_migrate_all = False
    # Reset the initial run value
    cache.ram("initial_run", lambda: False, time_expire=0)


# Starts in the Models folder
w2py_folder = os.path.abspath(__file__)
# print "Running File: " + app_folder
w2py_folder = os.path.dirname(w2py_folder)
# app folder
w2py_folder = os.path.dirname(w2py_folder)
app_folder = w2py_folder
# Applications folder
w2py_folder = os.path.dirname(w2py_folder)
# Root folder
w2py_folder = os.path.dirname(w2py_folder)


if not request.env.web2py_runtime_gae:
    # if NOT running on Google App Engine use SQLite or other DB
    # db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'], lazy_tables=lazy_tables,
    #  fake_migrate_all=fake_migrate ) # lazy_tables=True   , fake_migrate_all=True
    # db = DAL(myconf.get('db.uri'),
    #         pool_size=myconf.get('db.pool_size'),
    #         migrate_enabled=myconf.get('db.migrate'),
    #         check_reserved=['all'])
    
    db = DAL(myconf.get('db.uri'), pool_size=myconf.get('db.pool_size'), check_reserved=['all'],
             migrate_enabled=migrate_enabled,
             lazy_tables=lazy_tables, fake_migrate=fake_migrate, fake_migrate_all=fake_migrate_all,
             migrate=migrate )  # fake_migrate_all=True
    db.executesql('PRAGMA journal_mode=WAL')
    
    db_scheduler = DAL('sqlite://storage_scheduler.sqlite', pool_size=0, check_reserved=['all'])
    db_scheduler.executesql('PRAGMA journal_mode=WAL')

    db_laptops = DAL('sqlite://storage_laptops.sqlite', pool_size=0, check_reserved=['all'])
    db_laptops.executesql('PRAGMA journal_mode=WAL')

    #db_lti = DAL('sqlite://storage_lti.sqlite', pool_size=0, check_reserved=['all'])
    #db_lti.executesql('PRAGMA journal_mode=WAL')
    import psycopg2
    import psycopg2.extensions
    from urllib.parse import quote_plus
    pg_server = quote_plus(myconf.get('pg_db.pg_server'))
    pg_port = myconf.get('pg_db.pg_port')
    pg_database = quote_plus(myconf.get('pg_db.pg_database'))
    pg_user = quote_plus(myconf.get('pg_db.pg_user'))
    pg_pass = myconf.get('pg_db.pg_pass')
    if pg_pass == "<IT_PW>":
        # Grab from the environment
        pg_pass = quote_plus(os.environ.get('IT_PW', 'INVALID_PASSWORD'))
    pg_pass = quote_plus(pg_pass)
    pg_migrate = myconf.get('pg_db.pg_migrate')
    pg_uri = f"postgres://{pg_user}:{pg_pass}@{pg_server}:{pg_port}/{pg_database}"
    if pg_server is None:
        print("ERROR - No Postgres server specified!!!")
    #print(f"PG URI: {pg_uri}")
    db_lti_try_again = False
    try:
        db_lti = DAL(pg_uri, pool_size=10, check_reserved=['all'], migrate=pg_migrate, decode_credentials=True)

    except Exception as ex:
        # If database does not exist, create it.
        if f"database \"{pg_database}\" does not exist" in str(ex):
            print(f"Database {pg_database} does not exist, trying to create it...")
            tmp_uri = f"postgres://{pg_user}:{pg_pass}@{pg_server}:{pg_port}/postgres"
            tmp_db = psycopg2.connect(tmp_uri) #DAL(tmp_uri, pool_size=1, check_reserved=['all'], migrate=False, decode_credentials=True)
            # Need this to run DDL statements
            tmp_db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            # See if the database exists
            cursor = tmp_db.cursor()
            rs = cursor.execute(f"SELECT * FROM pg_database WHERE datname='{pg_database}'")
            if rs is None:
                # No records - try to create the database
                cursor.execute(f"CREATE DATABASE {pg_database} WITH OWNER = {pg_user} ENCODING = 'UTF8' CONNECTION LIMIT = -1 IS_TEMPLATE = False;")
            else:
                # Records exist - database exists
                print(f"DB Exists! {pg_database}")
                
            cursor.close()
            tmp_db.close()

            db_lti_try_again = True
            
    if db_lti_try_again:
        # Try again to connect to the database
        try:
            db_lti = DAL(pg_uri, pool_size=10, check_reserved=['all'], migrate=pg_migrate, decode_credentials=True)
        except Exception as ex:
            print("ERROR - Unable to connect to postgresql database!")
            raise HTTP(500, "ERROR - Unable to connect to postgreql database!")
        
    # Try to use redis for session caching if available, fall back to normal file based.
    try_redis_sessions = cache.ram("try_redis_sessions", lambda: True, time_expire=36000)
    #print(f"Use For Sessions {myconf.get('redis.use_for_sessions')}")
    if request.is_scheduler is not True and try_redis_sessions and myconf.get('redis.use_for_sessions'):
        cache.ram("try_redis_sessions", lambda: False, time_expire=0)

        from gluon.contrib.redis_utils import RConn
        from gluon.contrib.redis_session import RedisSession
        try:
            rconn = RConn(
                host=myconf.get('redis.host'),
                port=myconf.get('redis.port'),
                db=myconf.get('redis.db'),
                socket_connect_timeout=2,
            )
            # Make sure we can use this, if not fall back to no redis support.
            rconn.ping() # will hit exception if it fails and fall back to normal sessions
            sessiondb = RedisSession(redis_conn=rconn, session_expiry=3600, with_lock=False)  # with_lock=True to force locking of session between concurrent requests
            session.connect(request, response, db=sessiondb)            
        except Exception as ex:
            print(f"Error using Redis for sessions, disabling for now.\n-> {ex}")

else:
    # connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    # store sessions and tickets there
    session.connect(request, response, db=db)
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))

# Make sure sessions only work over HTTPS
session.secure()
## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else ['*.json']
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
# auth = Auth(db)
# auth = Auth(db, host_names=myconf.get('host.names'))
auth = Auth(db, hmac_key=Auth.get_or_create_key(), signature=True)  # secure=True
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=True)  # signature=False
auth.settings.create_user_groups = False

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

## configure auth policy
# auth.settings.actions_disabled = ['register', 'request_reset_password']
auth.settings.actions_disabled = ['register', 'change_password', 'request_reset_password',
                                  'retrieve_username', 'profile']
# you don't have to remember me
auth.settings.remember_me_form = False
##  auth.settings.actions_disabled=['change_password','request_reset_password','retrieve_username','profile']
##if request.controller != 'appadmin':
##    auth.settings.actions_disabled +=['register']
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.expiration = 7200  # 2 hrs

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
#from gluon.contrib.login_methods.rpx_account import use_janrain
#use_janrain(auth, filename='private/janrain.key')


# Add basic auth
#from gluon.contrib.login_methods.basic_auth import basic_auth
#auth.settings.login_methods.append(
#    basic_auth('OPE - SMC'))


#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
auth.enable_record_versioning(db)

from gluon import current
current.db = db
current.db_scheduler = db_scheduler
current.db_laptops = db_laptops
current.migrate = migrate
current.db_lti = db_lti
current.auth = auth
current.smc_log = ""
current.config = myconf
current.session = session
current.cache = cache
