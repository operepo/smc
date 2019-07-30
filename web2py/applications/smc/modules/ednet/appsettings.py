# -*- coding: utf-8 -*-

from gluon import *
from gluon import current

###### Settings Class
class AppSettings:

    def __init__(self):
        pass

    @staticmethod
    def SetValue(key, value):
        db = current.db # Grab current db object

        items = {key: value}
        db(db.my_app_settings).update(**items)
        db.commit()

    @staticmethod
    def GetValue(key, default):
        db = current.db # Grab the current db object
        ret = ""

        settings = dict()

        if (len(settings) < 1):
            # Need to load the settings
            rows = db(db.my_app_settings).select(limitby=(0,1))
            for row in rows:
                for col in db.my_app_settings.fields:
                    settings[col] = row[col]
        
        if (key in settings):
            if (settings[key] != None and len(str(settings[key])) > 0):
                ret = settings[key] # t1
            else:
                ret = default
        else:
            ret = default
            
        return ret
    
###### End MySettings
