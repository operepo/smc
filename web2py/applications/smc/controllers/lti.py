#from pylti1p3.tool_config import ToolConfJsonFile
#tool_conf = ToolConfJsonFile('path/to/json')
# from pylti1p3.tool_config import ToolConfDict
# settings = {
#     "iss1": [
#         {
#             "default": True,
#             "client_id": "client_id1",  # Recieved from canvas in aud
#             "auth_login_url": "",
#             "auth_token_url": "",
#             "auth_audience": None,
#             "key_set_url": "",
#             "key_set": None,
#             "private_key_file": "private.key",
#             "public_key_file": "public.key",
#             "deployment_ids": ["id1", "id2"],
#         }
#     ],
# }
# private_key = '...'
# public_key = '...'
# tool_conf = ToolConfDict(settings)

# client_id = '...'
# tool_conf.set_private_key(iss, private_key, client_id=client_id)
# tool_conf.set_public_key(iss, public_key, client_id=client_id)

import json
from gluon import current

def rce_insert_video():
    # Required for cookies to work in LTI land
    session.samesite('none')

    return_url = request.vars.get("launch_presentation_return_url", None)
    if return_url is None:
        # Try loading from the session.
        return_url = session.get("return_url", "#")
    session.return_url = return_url

    ret = dict()
    ret['vars'] = XML("<pre>" + json.dumps(request.vars, indent=4) + "</pre>")
    
    return ret

def rce_insert_video_ajax():
    # Required for cookies to work in LTI land
    session.samesite('none')

    #response.view = 'generic.html'
    ret = dict()

    return_url = session.get("return_url", "#")
    
    # search_box = INPUT(_name="search_box", _id="search_box", _style="width: 450px;")
    # form = FORM(TABLE(TR("Video Search: ", search_box),
    #                   TR("", INPUT(_type="submit", _value="Search"))), _name="search_form").process(formname="search_form",
    #                                                                                            keepvalues=True)
    
    # if form.accepted:
    #     search_text = form.vars.search_box

    query = (db.media_files)
    links = []
    # if auth.has_membership('Faculty') or auth.has_membership('Administrators'):
    #     links.append(dict(header=T(''),body=lambda row: (
    #         A('[Edit]', _style='font-size: 10px; color: red;', _href=URL('media', 'edit_media', args=[row.media_guid], user_signature=True)),
    #         ' | ',
    #         A('[Delete]', _style='font-size: 10px; color: red;', _href=URL('media', 'delete_media', args=[row.media_guid], user_signature=True)),
    #         ) ) )
    #     #links.append(dict(header=T(''),body=lambda row:  ) )
    #links.append(dict(header=T(''),body=lambda row: IMG(_src=get_cc_icon(row.media_guid), _style="width: 24px; height: auto; max-width: 24px;", _alt="Close Captioning Available")))
    links.append(
        dict(header=T(''), 
            body=lambda row: (A('[Embed]', _style='font-size: 10px; color:red;',
            _href=f"{return_url}?return_type=iframe&title={row.title}&width=650&height=405&url=" + URL('media', 'player.load', args=[row.media_guid], host=True)))
        )
    )
    links.append(dict(header=T(''),body=lambda row: A(IMG(_src=getMediaThumb(row.media_guid), _style="width: 128px; height: auto; max-width: 128px;"),
        _href=f"{return_url}?return_type=iframe&title={row.title}&width=650&height=405&url=" + URL('media', 'player.load', args=[row.media_guid], host=True)
        ) ) )
    fields = [db.media_files.id, db.media_files.title, db.media_files.tags, db.media_files.description, db.media_files.media_guid, db.media_files.category] #[db.media_files.title]
    maxtextlengths = {'media_files.title': 150, 'media_files.tags': 50, 'media_files.description': 150}
    
    # Hide columns
    db.media_files.id.readable=False
    db.media_files.media_guid.readable=False
    db.media_files.width.readable=False
    db.media_files.height.readable=False
    db.media_files.original_file_name.readable=False
    db.media_files.media_type.readable=False
    db.media_files.quality.readable=False
    db.media_files.description.readable=False
    db.media_files.category.readable=False
    db.media_files.tags.readable=False
    
    # rows = db(query).select()
    media_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.media_files.modified_on],
                              fields=fields, paginate=15, user_signature=False,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)
    
    ret["media_grid"] = media_grid

    return ret


# Fetch quiz questions and pack them up into an encrypted package
def student_quizzes(): #lti=lti):  # Flask param - use on web2py??
    # Required for cookies to work in LTI land
    session.samesite('none')

    response.view = 'generic.json'
    ret = dict()

    # Check oauth to make sure anon users don't hit the service
    # from pylti.flask import lti  Add decorator
    # @lti(request='initial', error=error, app=app)
    # Has PYLTI_CONFIG { "consumers": { os.environ.get("CONSUMER_KEY", "CHANGEME"): { "secret": os.environ.get("LTI_SECRET", "CHANGEME")}}}



    # Will need the launch return url:
    return_url = request.vars.get("launch_presentation_return_url", '#')
    # To return a response:....
    # return_url + "?return_type=image_url&url=https://???.img.png&alt=icontitle"  # To send back an image
    ret = request.vars

    
    return "<pre>" + json.dumps(ret, indent=4) + "</pre>"