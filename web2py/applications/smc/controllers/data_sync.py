# -*- coding: utf-8 -*-
### Data Sync Controller
###   Api for interfacing with data_sync app where data is actually saved
###     Used to expose authentication and session setup (master server)
###

from gluon import current

# Help shut up pylance warnings
if 1==2: from ..common import *

# Required to use basic authentication
auth.settings.allow_basic_login = True

#response.view = 'generic.json'

def index():
    response.view = 'generic.json'
    return dict(message="Data Sync Controller")



# Normal user/pass authentication
def authenticate():
    response.view = 'generic.json'
    ret = False

    return dict(ret=ret)

def authenticate_with_key():
    response.view = 'generic.json'
    ret = False
    return dict(ret=ret)
