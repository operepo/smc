# -*- coding: utf-8 -*-
import os
from ednet.ad import AD

# Help shut up pylance warnings
if 1==2: from ..common import *

# Do we need to do initial init? (e.g. creating indexes.....)
db_init_needed = cache.ram('db_init_needed', lambda: True, time_expire=3600)

## Make sure that these entries are present in the database
# Groups
if db_init_needed and db(db.auth_group.id > 0).count() == 0:
   db.auth_group.insert(role='Administrators', description='Users with administrative privileges')
   db.auth_group.insert(role='Import', description='Users with import privileges')
   db.auth_group.insert(role='Students', description='Users with student privileges')
   db.auth_group.insert(role='Faculty', description='Faculty members')
   db.commit()

if db_init_needed:
    g = db(db.auth_group.role=='Media Upload').select().first()
    if (g == None):
        db.auth_group.insert(role='Media Upload', description='Users with permission to upload media files')
    g = db(db.auth_group.role=='Laptop Logs').select().first()
    if (g == None):
        db.auth_group.insert(role='Laptop Logs', description='Users with permission to view laptop log files')
    
    # Make sure permissions are setup for each group
    auth.add_permission(name='credential', group_id=auth.id_group(role='Administrators'))
    auth.add_permission(name='credential', group_id=auth.id_group(role='Faculty'))

    # Make sure we set some defaults for new settings fields so we don't end up with nulls    
    db(db.my_app_settings.laptop_network_type == None).update(laptop_network_type="Standalone")
    db(db.my_app_settings.laptop_domain_name == None).update(laptop_domain_name="SBCTC.local")
    db(db.my_app_settings.laptop_domain_ou == None).update(laptop_domain_ou="laptopOU.SBCTC.local")
    db(db.my_app_settings.laptop_admin_account == None).update(laptop_admin_account="huskers")
    db(db.my_app_settings.laptop_time_servers == None).update(laptop_time_servers=["time.windows.com"])
    db(db.my_app_settings.laptop_approved_nics == None).update(laptop_approved_nics=[])


    db.commit()

    # Make sure versions are all 0 (no nulls)
    db(db.document_files.item_version == None).update(item_version=0)
    db(db.media_files.item_version == None).update(item_version=0)
    db.commit()

new_admin = False
# Starting Users
if db_init_needed and db(db.auth_user.id > 0).count() == 0:
    db.auth_user.insert(
        first_name='admin',
        last_name='admin',
        email='admin@correctionsed.com',
        username='admin',
        password='sha512$879808aa38f13af4$9eb1bdf5159c075f5a7f3bb4cf73fa2acbee1f25351badf3e3417f0f32010bcdc3a746974150c7fe2ea780ee4aad8cda457236853f1fa60a0a9097c15d721bb8',
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
        # print("Resetting admin password...")
        # Set pw for w2p admin login (parameters_??.py file)
        save_password(pw,80)
        save_password(pw,443)
        # Set pw for smc admin login (in the database)
        db(db.auth_user.username=='admin').update( password=db.auth_user.password.validate(pw)[0] )
        db.commit()
    # Set the cache with the new value
    cache.ram('startup', lambda: False, 0)


if db_init_needed:
    # Mark that we did it so we quit doing it on every page view
    cache.ram('db_init_needed', lambda: False, 0)
    




"""
Don't use this - using pytubefix instead
"""
"""
this is pytube monkey fix, just adapter youtube js change
[!TIPS]: u can chat with chatGPT to fix it, use js code and bug info
"""
# import logging
# import re
# from typing import List

# from pytube import YouTube, cipher
# from pytube.innertube import _default_clients
# from pytube.exceptions import RegexMatchError

# YouTube = YouTube

# # issue: https://github.com/pytube/pytube/issues/1973
# _default_clients["ANDROID"]["context"]["client"]["clientVersion"] = "19.08.35"
# _default_clients["IOS"]["context"]["client"]["clientVersion"] = "19.08.35"
# _default_clients["ANDROID_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
# _default_clients["IOS_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
# _default_clients["IOS_MUSIC"]["context"]["client"]["clientVersion"] = "6.41"
# _default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]


# def get_throttling_function_name(js: str) -> str:
#     """Extract the name of the function that computes the throttling parameter.

#     :param str js:
#         The contents of the base.js asset file.
#     :rtype: str
#     :returns:
#         The name of the function used to compute the throttling parameter.
#     """
#     function_patterns = [
#         r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
#         r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&\s*'
#         r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
#         r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',

#     ]
#     # logging.debug('Finding throttling function name')
#     for pattern in function_patterns:
#         regex = re.compile(pattern)
#         function_match = regex.search(js)
#         if function_match:
#             logging.debug("finished regex search, matched: %s", pattern)
#             if len(function_match.groups()) == 1:
#                 return function_match.group(1)
#             idx = function_match.group(2)
#             if idx:
#                 idx = idx.strip("[]")
#                 array = re.search(
#                     r'var {nfunc}\s*=\s*(\[.+?\]);'.format(
#                         nfunc=re.escape(function_match.group(1))),
#                     js
#                 )
#                 if array:
#                     array = array.group(1).strip("[]").split(",")
#                     array = [x.strip() for x in array]
#                     return array[int(idx)]

#     raise RegexMatchError(
#         caller="get_throttling_function_name", pattern="multiple"
#     )


# cipher.get_throttling_function_name = get_throttling_function_name


# # https://github.com/pytube/pytube/issues/2006
# def get_transform_plan(js: str) -> List[str]:
#     """Extract the "transform plan".

#     The "transform plan" is the functions that the ciphered signature is
#     cycled through to obtain the actual signature.

#     :param str js:
#         The contents of the base.js asset file.

#     **Example**:

#     ['DE.AJ(a,15)',
#     'DE.VR(a,3)',
#     'DE.AJ(a,51)',
#     'DE.VR(a,3)',
#     'DE.kT(a,51)',
#     'DE.kT(a,8)',
#     'DE.VR(a,3)',
#     'DE.kT(a,21)']
#     """
#     name = re.escape(cipher.get_initial_function_name(js))
#     # pattern = r"%s=function\(\w\){[a-z=\.\(\"\)]*;(.*);(?:.+)}" % name
#     pattern = r"%s=function\(\w\){[a-z=\.\(\"\)]*;((\w+\.\w+\([\w\"\'\[\]\(\)\.\,\s]*\);)+)(?:.+)}" % name
#     logging.debug("getting transform plan")
#     return cipher.regex_search(pattern, js, group=1).split(";")


# cipher.get_transform_plan = get_transform_plan