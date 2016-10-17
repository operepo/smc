# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
request.requires_https()


lazy_tables = True
fake_migrate_all = False
fake_migrate = False
migrate = True

tmp = request.vars.lazy_tables
if (tmp):
    if (tmp.lower() == "false"):
        lazy_tables = False

tmp = request.vars.fake_migrate
if (tmp):
    if(tmp.lower() == "true"):
        fake_migrate = True
        migrate = False

tmp = request.vars.fix
if (tmp):
    if (tmp.lower() == "true"):
        lazy_tables = False
        fake_migrate = True
        migrate = False

# Check for firstrun file and force db migrate
#Starts in the Models folder
w2py_folder = os.path.abspath(__file__)
#print "Running File: " + app_folder
w2py_folder = os.path.dirname(w2py_folder)
# app folder
w2py_folder = os.path.dirname(w2py_folder)
app_folder = w2py_folder
# Applications folder
w2py_folder = os.path.dirname(w2py_folder)
# Root folder
w2py_folder = os.path.dirname(w2py_folder)
first_run = os.path.join(app_folder, ".first_run")
if (os.isfile(first_run):
	# First run file exists
	lazy_tables = False
	fake_migrate = True
	migrate = False
	# Remove the file so it doesn't keep running
	os.remove(first_run)
        
if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'], lazy_tables=lazy_tables, fake_migrate_all=fake_migrate ) # lazy_tables=True   , fake_migrate_all=True
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'], lazy_tables=lazy_tables, fake_migrate=fake_migrate, fake_migrate_all=fake_migrate_all, migrate=migrate ) # fake_migrate_all=True
    db.executesql('PRAGMA journal_mode=WAL')
    
    db_scheduler = DAL('sqlite://storage_scheduler.sqlite', pool_size=1, check_reserved=['all'])
    db_scheduler.executesql('PRAGMA journal_mode=WAL')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
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
#auth = Auth(db)
auth = Auth(db, hmac_key = Auth.get_or_create_key(), signature=True) #secure=True
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=True) #signature=False
auth.settings.create_user_groups=False

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'correctionsed.com:587'
mail.settings.sender = 'admin@correctionsed.com'
mail.settings.login = 'username:password'

## configure auth policy
#auth.settings.actions_disabled = ['register', 'request_reset_password']
auth.settings.actions_disabled=['register','change_password','request_reset_password','retrieve_username','profile']
# you don't have to remember me
auth.settings.remember_me_form = False
##  auth.settings.actions_disabled=['change_password','request_reset_password','retrieve_username','profile']
##if request.controller != 'appadmin':
##    auth.settings.actions_disabled +=['register']
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

# ldap authentication and not save password on web2py
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
#auth.settings.login_methods = [ldap_auth(mode='ad',
#                                         bind_dn="cn=huskers,ou=users,dc=cbcc,dc=pencollege,dc=net",
#                                         bind_pw="abc123",
#    db=db,
#    server='206.111.5.2',
#    base_dn='ou=Users,dc=cbcc,dc=pencollege,dc=net',
#    logging_level='debug')] #,auth]
#pass

#['ou=Users,dc=cbcc,dc=pencollege,dc=net','ou=Students,dc=cbcc,dc=pencollege,dc=net']))
#group=, goup_name_attrib='cn',

#auth.settings.login_methods = [ldap_auth(mode='ad',
#    manage_groups= True, 
#    db = db,
#    group_name_attrib = 'cn',
#    group_member_attrib = 'member',
#    group_filterstr = 'objectClass=Group',
#    server='<server>',
#    base_dn='OU=<my org unit>,DC=<domain>,DC=<domain>')]

#auth.settings.login_methods = [ldap_auth(mode="ad", server=settings.ldap_server, base_dn=settings.domain_name, db=db,
#                                    manage_user=True,
#                                    user_firstname_attrib="givenName",
#                                    user_lastname_attrib="sn",
#                                    user_mail_attrib="mail",
#                                    manage_groups=True,
#                                    group_dn="ou=Groups," + settings.domain_name,
#                                    group_name_attrib="cn",
#                                    group_member_attrib="member",
#                                    group_filterstr='objectClass=*')]

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
current.auth = auth
current.smc_log = ""

# Track module changes
from gluon.custom_import import track_changes
#track_changes(True)

