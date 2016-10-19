# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

##response.logo = A(B('web',SPAN(2),'py'),XML('&trade;&nbsp;'),
##                  _class="brand",_href="http://www.web2py.com/")
response.logo = IMG(_src=URL('static','images/pc_logo.png'), _alt="Peninsula College", _class="brand",_style="height: 30px;")
response.title = request.application.replace('_',' ').title()
response.subtitle = 'Student Management Console - Import/Enrollment for Active Directory and Canvas'

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Ray Pulsipher <ray@correctionsed.com>'
response.meta.keywords = 'admin, student, sms, import, canvas, active directory, peninsula college web2py, python, framework'
response.meta.generator = 'Web2py Web Framework'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Home'), False, URL('default', 'index'), []),
	(T('Media'), False, URL('media', 'index'), [
			(T('Media Library'), False, URL('media','index')),
			#(T('Playlists'), False, URL('media','playlists')),
			(T('Upload Media'), False, URL('media','upload_media')),
			(T('WAMAP Import'), False, URL('media','wamap_import')),
		]),
    (SPAN('Students', _class='highlighted'), False, URL('student', 'index'), [
            (T('Change Password'), False, URL('student','changepassword'))
        ]),
    (SPAN('Faculty', _class='highlighted'), False, URL('faculty', 'index'), [
			(T('Change Password'), False, URL('faculty', 'changepassword')),
			(T('Manage Students'), False, URL('faculty', 'manage_students')),
			(T('Manage Faculty'), False, URL('faculty', 'manage_faculty')),
		]),
    (SPAN('Import', _class='highlighted'), False, URL('import', 'index'), [
            (T('Import Students'), False, URL('import', 'student_pick_excel')),
            (T('Import Faculty'), False, URL('import', 'faculty_pick_excel'))
        ]),
    (SPAN('Admin', _class='highlighted'), False, URL('admin', 'index'), [
            (T('Change Password'), False, URL('admin', 'changepassword')),
            (T('Configure App'), False, URL('admin', 'config'), [
				(T('App Settings'), False, URL('admin', 'config_app_settings')),
				(T('Active Directory Settings'), False, URL('admin', 'config_ad_settings')),
				(T('File Server Settings'), False, URL('admin', 'config_file_settings')),
				(T('Faculty Settings'), False, URL('admin', 'config_faculty_settings')),
				(T('Student Settings'), False, URL('admin', 'config_student_settings')),
				(T('Canvas Settings'), False, URL('admin', 'config_canvas_settings')),
                (T('ZFS Settings'), False, URL('admin', 'config_zfs_settings')),
			 ]),
            #(T('Manage Users'), False, URL('admin', 'users')),
			(T('Switch Mode'), False, URL('admin', 'switchmode')),
			(T('Switch AD Quota'), False, URL('admin', 'switchquota')),
			(T('Reset SMC'), False, URL('admin', 'reset_smc')),
        ]),
    #(SPAN('Documentation', _class='highlighted'), False, URL('docs', 'index'), [
    #        (T('Getting Started'), False, URL('docs', 'index'))
    #   ])
]

DEVELOPMENT_MENU = False

#########################################################################
## provide shortcuts for development. remove in production
#########################################################################

def _():
    # shortcuts
    app = request.application
    ctr = request.controller
    # useful links to internal and external resources
    #response.menu += [
    #    (SPAN('Students', _class='highlighted'), False, URL('student', 'index'), [
    #        (T('Change Password'), False, URL('student','changepassword'))
    #    ]),
    #    (SPAN('Faculty', _class='highlighted'), False, URL('faculty', 'index'), []),
    #    (SPAN('Import', _class='highlighted'), False, URL('import', 'index'), []),
    #    (SPAN('Admin', _class='highlighted'), False, URL('admin', 'index'), [])
    #    ]
    """ response.menu += [
        (SPAN('web2py', _class='highlighted'), False, 'http://web2py.com', [
        (T('My Sites'), False, URL('admin', 'default', 'site')),
        (T('This App'), False, URL('admin', 'default', 'design/%s' % app), [
        (T('Controller'), False,
         URL(
         'admin', 'default', 'edit/%s/controllers/%s.py' % (app, ctr))),
        (T('View'), False,
         URL(
         'admin', 'default', 'edit/%s/views/%s' % (app, response.view))),
        (T('Layout'), False,
         URL(
         'admin', 'default', 'edit/%s/views/layout.html' % app)),
        (T('Stylesheet'), False,
         URL(
         'admin', 'default', 'edit/%s/static/css/web2py.css' % app)),
        (T('DB Model'), False,
         URL(
         'admin', 'default', 'edit/%s/models/db.py' % app)),
        (T('Menu Model'), False,
         URL(
         'admin', 'default', 'edit/%s/models/menu.py' % app)),
        (T('Database'), False, URL(app, 'appadmin', 'index')),
        (T('Errors'), False, URL(
         'admin', 'default', 'errors/' + app)),
        (T('About'), False, URL(
         'admin', 'default', 'about/' + app)),
        ]),
            ('web2py.com', False, 'http://www.web2py.com', [
             (T('Download'), False,
              'http://www.web2py.com/examples/default/download'),
             (T('Support'), False,
              'http://www.web2py.com/examples/default/support'),
             (T('Demo'), False, 'http://web2py.com/demo_admin'),
             (T('Quick Examples'), False,
              'http://web2py.com/examples/default/examples'),
             (T('FAQ'), False, 'http://web2py.com/AlterEgo'),
             (T('Videos'), False,
              'http://www.web2py.com/examples/default/videos/'),
             (T('Free Applications'),
              False, 'http://web2py.com/appliances'),
             (T('Plugins'), False, 'http://web2py.com/plugins'),
             (T('Layouts'), False, 'http://web2py.com/layouts'),
             (T('Recipes'), False, 'http://web2pyslices.com/'),
             (T('Semantic'), False, 'http://web2py.com/semantic'),
             ]),
            (T('Documentation'), False, 'http://www.web2py.com/book', [
             (T('Preface'), False,
              'http://www.web2py.com/book/default/chapter/00'),
             (T('Introduction'), False,
              'http://www.web2py.com/book/default/chapter/01'),
             (T('Python'), False,
              'http://www.web2py.com/book/default/chapter/02'),
             (T('Overview'), False,
              'http://www.web2py.com/book/default/chapter/03'),
             (T('The Core'), False,
              'http://www.web2py.com/book/default/chapter/04'),
             (T('The Views'), False,
              'http://www.web2py.com/book/default/chapter/05'),
             (T('Database'), False,
              'http://www.web2py.com/book/default/chapter/06'),
             (T('Forms and Validators'), False,
              'http://www.web2py.com/book/default/chapter/07'),
             (T('Email and SMS'), False,
              'http://www.web2py.com/book/default/chapter/08'),
             (T('Access Control'), False,
              'http://www.web2py.com/book/default/chapter/09'),
             (T('Services'), False,
              'http://www.web2py.com/book/default/chapter/10'),
             (T('Ajax Recipes'), False,
              'http://www.web2py.com/book/default/chapter/11'),
             (T('Components and Plugins'), False,
              'http://www.web2py.com/book/default/chapter/12'),
             (T('Deployment Recipes'), False,
              'http://www.web2py.com/book/default/chapter/13'),
             (T('Other Recipes'), False,
              'http://www.web2py.com/book/default/chapter/14'),
             (T('Buy this book'), False,
              'http://stores.lulu.com/web2py'),
             ]),
            (T('Community'), False, None, [
             (T('Groups'), False,
              'http://www.web2py.com/examples/default/usergroups'),
                        (T('Twitter'), False, 'http://twitter.com/web2py'),
                        (T('Live Chat'), False,
                         'http://webchat.freenode.net/?channels=web2py'),
                        ]),
                (T('Plugins'), False, None, [
                        ('plugin_wiki', False,
                         'http://web2py.com/examples/default/download'),
                        (T('Other Plugins'), False,
                         'http://web2py.com/plugins'),
                        (T('Layout Plugins'),
                         False, 'http://web2py.com/layouts'),
                        ])
                ]
         )]
         """
if DEVELOPMENT_MENU: _()

if "auth" in locals(): auth.wikimenu()
