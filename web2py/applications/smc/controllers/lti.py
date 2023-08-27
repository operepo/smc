import os
import uuid
import json
from gluon import current
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.exception import LtiException

import traceback

from ednet.canvas import Canvas



# Help shut up pylance warnings
if 1==2: from ..common import *


def oidc_login():
    # Required for cookies to work in LTI land
    session.samesite('none')

    # from pylti1p3.oidc_login import OIDCLogin
    # oidc_login = OIDCLogin(request, tool_conf) 
    ret = None
    print(f"OIDC_LTI Login attempted.")
    print(f"OIDC Vars: {request.vars}")
    print(f"OIDC Args: {request.args}")

    tool_conf = get_lti_tool_config()
    print(f"ToolConf: {tool_conf.__dict__}")

    lti_request = W2PyRequest()
    try:
        oidc_login = W2PyOIDCLogin(lti_request, tool_conf)
        oidc_login.enable_check_cookies()
    except Exception as ex:
        return "ERROR"

    target_uri = request.vars.target_link_uri
    if target_uri is None:
        print("LTI - Redirecting to /index")
        target_uri = "/index"
    print(request.vars)

    iss = None
    for key in tool_conf.__dict__['_config'].keys():
        iss = key
        break

    
    try:
        # Need to make authorize URL.
        #auth_url = "https://canvas.instructure.com/api/lti/authorize_redirect?"

        auth_url = request.vars['iss']
        if 'saltire' in auth_url:
            auth_url += "/auth?"
        elif 'canvas' in auth_url:
            auth_url += "/api/lti/authorize_redirect?"

        auth_url += f"client_id={request.vars['client_id']}"  # "tool_conf['_config'][0]['client_id']}"
        auth_url += f"&response_type=id_token" # OidcConstants.ResponseTyps.IdToken
        auth_url += f"&response_mode=form_post"
        auth_url += f"&redirect_uri={target_uri}"
        auth_url += f"&scope=openid" # OidcConstants.StandardScopes.OpenId
        auth_url += f"&state={uuid.uuid4()}"  # Session ID
        auth_url += f"&login_hint={request.vars['login_hint']}"
        auth_url += f"&lti_message_hint={request.vars['lti_message_hint']}"
        auth_url += f"&nonce={uuid.uuid4()}"            # Check nonce at launch to make sure id_token came from this flow
        auth_url += f"&prompt=none"             # No user interaction
        #auth_url += f"&extra=lti_message_hint={LtiMessageHint}" # Resource link id or deep link id
    
        # Do redirect manually
        #lti_response = oidc_login.redirect(target_uri)
        #redirect_obj = oidc_login.get_redirect_object(target_uri)
        redirect_url = oidc_login.get_redirect(auth_url)
        
        #redirect(redirect_url)
    except Exception as ex:
        traceback.print_exc()
        traceback.print_stack()
        raise HTTP(500, f"Failed to authenticate OAuth2 - {ex}", location=URL('lti_launch'))
    
    redirect_url.do_redirect()
    #print("abc")
    return ret


def lti_tool_config():
    # Required for cookies to work in LTI land
    session.samesite('none')

    response.view = 'generic.json'
    response.headers['Content-Type'] = "application/json"
    
    tool_config = get_lti_tool_config_json()
    print(f"lti_tool_config: {tool_config}")
    return tool_config

def lti_launch():
    # Required for cookies to work in LTI land
    session.samesite('none')

    ret = None
    tool_conf = get_lti_tool_config()
    req = W2PyRequest(request)

    print(f"Posted Values: \nArgs: {request.args}\nVars: {request.vars}")
    print(f"State: request. {request.vars['state']}")
    try:
        message_launch = W2PyMessageLaunch(req, tool_conf)
        #message_launch.set_auto_validation(enable=False)
        launch_data = message_launch.get_launch_data()
        if message_launch.is_resource_launch():
            ret = "Resource Launch"
        elif message_launch.is_deep_link_launch():
            ret = "Deep Link Launch"
        else:
            ret = "Invalid launch type!"
        
    except LtiException as ex:
        print(f"ERROR - Bad LTI launch\n{ex}")
        traceback.print_exc()
        traceback.print_stack()
        HTTP(500, f"ERROR - Bad LTI Launch: {ex}")

    print(f"LTI Launch - {ret}")
    return ret
    print(f"LTI Launch attempted.")

    
    lti_request = W2PyRequest()
    try:
        oidc_login = W2PyOIDCLogin(lti_request, tool_conf)
        oidc_login.enable_check_cookies()
    except Exception as ex:
        return "ERROR"

    target_uri = request.vars.target_link_uri
    if target_uri is None:
        print("LTI - Redirecting to /index")
        target_uri = "/index"
    print(request.vars)
    try:
        # Do redirect manually
        #lti_response = oidc_login.redirect(target_uri)
        redirect_obj = oidc_login.get_redirect_object(target_uri)
        redirect_url = oidc_login.get_redirect_url()
        redirect(redirect_url)
    except Exception as ex:
        traceback.print_exc()
        traceback.print_stack()
        raise HTTP(500, f"Failed to authenticate OAuth2 - {ex}", location=URL('lti_launch'))
    print("abc")
    return ret


def jwks():
    # Required for cookies to work in LTI land
    session.samesite('none')

    """
    Expose JWKS Public key and make it available to the LMS
    """
    response.view = 'generic.json'
    response.headers['Content-Type'] = "application/json"

    ret = dict()
    ret['keys'] = list()

    try:
        keys = get_lti_keys()
        for (jwks_str, public_key, private_key) in keys:
            ret['keys'].append(json.loads(jwks_str))
    except Exception as ex:
        ret['msg'] = f"ERROR - Unable to retrive JWKS keys {ex}"
        print(f"/lti/jwks - ERROR - Unable to retrieve JWKS keys\n{ex}")
        traceback.print_exc()

    return ret

"""
LTI 1.3 
- Hit launch URL - do openid verfication
- Redirect to proper location (quiz, staff_quiz, etc..)

DB Tables:
lti_key_set                         ( id - uuid/string not null pk)

lti_key(
    id                              uuid/string not null pk
    key_set_id                      (fk lti_key_set)
    private_key                     text not null
    alg                             text not null
)

lti_registration (
    id                              uuid/string not null
    issuer                          text not null
    client_id                       text not null
    platform_login_auth_endpoint    text not null
    platform_service_auth_endpoint  text not null
    platform_jwks_endpoint          text not null
    platform_auth_provider          text
    key_set_id                      uuid/string not null (fk lti_key_set)

    index - unique (issuer, client_id)
)

lti_deployment (

)


"""





"""
Auto Configure Steps:
- Create the developer key in the canvas database
This has to be a direct connection to the database, or be set manually.

- Add the external tool via Rest API - use the proper id for the developer key,
this should cause canvas to go to the SMC link where it can get the JSON to configure itself.


"""

def create_developer_key():
    # https://localhost:8000/lti/lti_tool_config.json

    return

@auth.requires_membership("Administrators")
def add_lti_tools_to_canvas():
    #response.view = 'generic.json'
    # Hit canvas and install the tools that are available in the SMC.
    ret = install_lti_tools()

    return ret


def rce_render_document_href(return_url, row):
    # Required for cookies to work in LTI land
    session.samesite('none')

    ret = ""
    # NOTE - using old RCE stuff - should get deep linking to work
    # https://canvas.instructure.com/doc/api/file.editor_button_tools.html
    import os, mimetypes
    from PIL import Image
    import urllib
    file_path = get_document_file_path(row.document_guid)

    width=height=0

    original_filename = row.original_file_name
    fname, ext = os.path.splitext(original_filename)
    mime_type = mimetypes.guess_type(original_filename)[0]
    ext = ext.lower()

    viewerjs_extensions = ['.pdf', '.odt', '.fodt', '.ott', '.odp', '.fodp', '.otp', '.ods', '.fods', '.ots']

    if mime_type.startswith("image/"):
        # Render as an image.
        if row.width is None or row.height is None:
            try:
                # Try opening the image to get width/height
                img = Image.open(file_path)
                width, height = img.size
            except Exception as ex:
                return ""
        else:
            width = row.width
            height = row.height
        
        ret = f"""{return_url}?return_type=image_url&title={urllib.parse.quote(row.title)}&alt={urllib.parse.quote(row.title) if row.description is None else urllib.parse.quote(row.description)}&width={width}&height={height}&url={urllib.parse.quote(URL('media', 'dl_document', args=[row.document_guid], host=True, extension=False))}"""
    elif ext in viewerjs_extensions:
        if not row.width is None and not row.height is None:
            width = row.width
            height = row.height
        else:
            width = "100%"
            height = "720"
        # Filter out % like width% so things encode properly
        width = urllib.parse.quote(width)
        height = urllib.parse.quote(height)
        ret = f"""{return_url}?return_type=iframe&title={row.title}&width={width}&height={height}&url={URL('static', 'ViewerJS/index.html', host=True, extension=False)+f"%23/media/dl_document/{row.document_guid}"}"""
    else:
        # Send back a download link
        ret = f"""{return_url}?return_type=url&title={urllib.parse.quote(row.title)}&text={urllib.parse.quote(row.title)}&url={urllib.parse.quote(URL('media', 'dl_document', args=[row.document_guid], host=True, extension=False))}"""
    
    return ret


def rce_insert_document_ajax():
    # Required for cookies to work in LTI land
    session.samesite('none')

    #response.view = 'generic.html'
    ret = dict()

    return_url = session.get("return_url", "#")
    
    query = (db.document_files)
    links = []
    
    links.append(
        dict(header=T(''), 
            body=lambda row: (A('[Embed]', _style='font-size: 10px; color:red;',
                                _href=rce_render_document_href(return_url, row) ))
        )
    )
    links.append(dict(header=T(''), body=lambda row: A(TABLE(TR(
                                                        TD(IMG(_src=getDocumentThumb(row.document_guid), _style="width: 24px;"),
                                                        _width=26),
                                                        TD(LABEL(row.title), _align="left")
                                                        )),
                                                        _href=rce_render_document_href(return_url, row)
                                                )))
    fields = [db.document_files.id, db.document_files.title, db.document_files.tags, db.document_files.description,
              db.document_files.document_guid, db.document_files.category, db.document_files.original_file_name,
              db.document_files.width, db.document_files.height]  # [db.document_files.title]
    maxtextlengths = {'document_files.title': 150, 'document_files.tags': 50, 'document_files.description': 150}

    # Hide columns
    db.document_files.id.readable = False
    db.document_files.title.listable = False
    db.document_files.title.searchable = True
    db.document_files.document_guid.readable = False
    db.document_files.original_file_name.readable = False
    db.document_files.media_type.readable = False
    db.document_files.description.readable=False
    db.document_files.category.readable=False
    db.document_files.tags.readable=False
    db.document_files.width.readable=False
    db.document_files.height.readable=False
    

    # rows = db(query).select()
    document_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.document_files.modified_on],
                              fields=fields, paginate=15,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)

    return dict(document_grid=document_grid)

def rce_insert_document():
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

def rce_insert_media():
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

def rce_insert_media_ajax():
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




# Quizzes jump point - redirect to student or admin from here
def quizzes():
    # Launch point - force LTI to re-init
    init_lti(force=True)

    redirect(URL('quiz_list'))


def api_delete_quiz():
    response.view = 'generic.json'
    ret = False
    quiz_id = request.args(0)

    if session.is_teacher or session.is_admin:
        quiz_item = db_lti(
            (db_lti.ope_quizzes.lms_parent_course==session.lti.get("custom_canvas_course_id", -1)) &
            (db_lti.ope_quizzes.id==quiz_id)
        ).select().first()
        if not quiz_item is None:
            #print(f"Trying to delete quiz: {quiz_id}")
            db_lti(db_lti.ope_quizzes.id==quiz_item.id).delete()
            db_lti.commit()
            ret = True
        else:
            ret = False
            print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to delete quiz: {quiz_id}")
    else:
        ret = False
        print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to delete quiz: {quiz_id}")
    
    return dict(ret=ret)

def api_toggle_quiz():
    response.view = 'generic.json'
    quiz_id = request.args(0)
    ret = False

    if session.is_teacher or session.is_admin:
        quiz_item = db_lti(
            (db_lti.ope_quizzes.lms_parent_course==session.lti.get("custom_canvas_course_id", -1)) &
            (db_lti.ope_quizzes.id==quiz_id)
        ).select().first()
        if not quiz_item is None:
            published = False if quiz_item.published==True else True
            #print(f"Trying to toggle/enable quiz: {quiz_id} {published}")
            
            r = db_lti(db_lti.ope_quizzes.id==quiz_item.id).update(
                published=published
            )
            #print(f"{r}")
            db_lti.commit()
            ret = True
        else:
            ret = False
            print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to toggle this quiz: {quiz_id}")
    else:
        ret = False
        print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to toggle this quiz: {quiz_id}")
    
    return dict(ret=ret)

def api_toggle_laptop():
    response.view = 'generic.json'
    quiz_id = request.args(0)
    ret = False

    if session.is_teacher or session.is_admin:
        quiz_item = db_lti(
            (db_lti.ope_quizzes.lms_parent_course==session.lti.get("custom_canvas_course_id", -1)) &
            (db_lti.ope_quizzes.id==quiz_id)
        ).select().first()
        if not quiz_item is None:
            available_on_offline_laptop = False if quiz_item.available_on_offline_laptop==True else True
            print(f"Trying to toggle/enable laptop quizzes: {quiz_id} {available_on_offline_laptop}")
            
            r = db_lti(db_lti.ope_quizzes.id==quiz_item.id).update(
                available_on_offline_laptop = available_on_offline_laptop
            )
            #print(f"{r}")
            db_lti.commit()
            ret = True
        else:
            ret = False
            print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to toggle this quiz for delivery on laptops: {quiz_id}")
    else:
        ret = False
        print(f"{session.lti.get('custom_canvas_user_login_id', '<UNKNOWN>')} is not allowed to toggle this quiz for delivery on laptops: {quiz_id}")
    
    return dict(ret=ret)

def api_get_ui_state():
    response.view = 'generic.json'
    # GetStored values in the session in response to UI changes
    # Params are /{control_id} - key=values are posted
    if len(request.args) < 1:
        print(f"api_set_ui_state - bad request - no control_id")
        return False
    
    control_id = request.args(0)
    if control_id is None:
        print(f"api_set_ui_state - bad request - no control_id")
        return False

    values = get_session_values(control=control_id)

    return dict(**values)

def api_set_ui_state():
    response.view = 'generic.json'
    # Store values in the session in response to UI changes
    # Params are /{control_id} - key=values are posted
    if len(request.args) < 1:
        print(f"api_set_ui_state - bad request - no control_id")
        return False
    
    control_id = request.args(0)
    if control_id is None:
        print(f"api_set_ui_state - bad request - no control_id")
        return False

    for key in request.vars:
        #print(f"api_set_ui_state ({control_id}): {key} -> {request.vars[key]}")
        
        set_session_value(control=control_id, key=key, value=request.vars[key])

    return True

def question_banks():
    if session.is_admin or session.is_teacher:
        class_query = (db_lti.ope_question_banks.lms_parent_course==session.lti.get("custom_canvas_course_id", -1))
    else:
        # Go away - if not a teacher, don't show anything!
        redirect(URL('lti', 'quizzes'))
        return None
    
    question_bank_rows = db_lti(
            (class_query)
            ).select(orderby=[db_lti.ope_question_banks.question_bank_position,db_lti.ope_question_banks.bank_title])

    # Note - use **quiz_types to expand it to key=value parameters when it is returned (e.g. html uses =assignment rather then quiz_types['assignment'])
    return dict(
        question_banks=question_bank_rows
        )


def quiz_list():
    slash_svg = """<svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-slash" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
  <path fill-rule="evenodd" d="M11.354 4.646a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708l6-6a.5.5 0 0 1 .708 0z"/>
</svg>"""

    checked_icon = "small inverted circular colored green check icon"
    unchecked_icon = "large ban icon"

    laptop_enabled_icon = "large colored green laptop icon"
    laptop_disabled_icon = "large disabled laptop icon"
    #laptop_dont_icon = "big dont icon"

    class_query = None
    if session.is_admin or session.is_teacher:
        class_query = (db_lti.ope_quizzes.lms_parent_course==session.lti.get("custom_canvas_course_id", -1))
    else:
        # Go away - if not a teacher, don't show anything!
        redirect(URL('lti', 'quizzes'))
        return None

    quiz_types = {
        "assignment": "(None)",
        "practice_quiz": "(None)",
        "graded_survey": "(None)",
        "survey": "(None)"
    }

    for quiz_type in quiz_types.keys():

        quiz_rows = db_lti(
            (class_query) & (db_lti.ope_quizzes.quiz_type==quiz_type)
            ).select(orderby=[db_lti.ope_quizzes.quiz_position,db_lti.ope_quizzes.title])

        t_rows = []
        
        for row in quiz_rows:
            published_toggle = unchecked_icon
            if row.published == True:
                published_toggle = checked_icon
            laptop_icon = laptop_disabled_icon
            laptop_slash_icon = slash_svg
            if row.available_on_offline_laptop == True:
                laptop_icon = laptop_enabled_icon
                laptop_slash_icon = ""

            tr = TR(
                TD(
                    XML(f"<div class='ui image' style='padding-left: 8px;'><img style='width: 24px;' src='{URL('static', 'images/quiz_icon.png')}' /></div>"),
                    _class="collapsing",
                    _onclick=f"window.location='{URL('lti', 'edit_quiz', args=[row.id])}';",
                ),
                TD(
                    XML(f"""
                        <h4>{row.title}</h4>
                        <span class="ui small text">{0 if row.points_possible is None else row.points_possible:.0f} pts / {row.question_count} Questions</span>
                    """),
                    _onclick=f"window.location='{URL('lti', 'edit_quiz', args=[row.id])}';",
                ),
                TD(

                    XML(
                    f"""
                        <button id="quiz_toggle_laptop_{row.id}" class="ui circular icon button toggle_laptop" style="background-color: transparent;"
                         data-quiz_id="{row.id}" data-quiz_id="{row.id}" data-content="Toggle Delivery On Laptops">
                            <i class="icons">
                                <i id="quiz_toggle_laptop_icon_{row.id}" class="{laptop_icon}"></i>
                                <i id="quiz_toggle_laptop_icon_slash_{row.id}" class="horizontally flipped huge disabled icon">{laptop_slash_icon}</i>
                            </i>
                        </button>
                        <button class="ui circular icon button toggle_quiz" style="background-color: transparent;"
                         data-quiz_id="{row.id}" data-content="Toggle Published Status">
                            <i class="{published_toggle}"></i>
                        </button>
                        <div class="ui dropdown" data-content="More Options (edit, delete)">
                            <i class="large ellipsis vertical icon"></i>
                            <div class="menu">
                                <div class="item" onclick="window.location='{URL('lti', 'edit_quiz', args=[row.id])}';" data-content="Edit Quiz Details or Questions"><i class="edit outline icon"></i>Edit</div>
                                <div class="item delete_quiz" onclick="return confirm_delete($(this), event);" data-quiz_id="{row.id}" data-quiz_title="{row.title}" data-content="Remove Quiz Permanently (No Undo)"><i class="trash alternate outline icon"></i>Delete</div>
                            </div>
                        </div>
                    """
                    ),
                    _class="collapsing",
                    _style="overflow: visible;"
                ),
                _style="overflow: visible; width: 100%",
                _id=f"quiz_row_{row.id}",
                _class=f"quiz_row",
            )
            t_rows.append(tr)

        if len(t_rows) > 0:
            quiz_types[quiz_type] = TABLE(
                TBODY(t_rows),
                _class="ui very basic collapsing table",
                _style="width: 100%; overflow: visible; padding:0px; margin:0px;"
            )

    # Note - use **quiz_types to expand it to key=value parameters when it is returned (e.g. html uses =assignment rather then quiz_types['assignment'])
    return dict(
        **quiz_types,
        checked_icon = checked_icon,
        unchecked_icon = unchecked_icon,
        laptop_enabled_icon = laptop_enabled_icon,
        laptop_disabled_icon = laptop_disabled_icon,
        laptop_slash_svg = XML(slash_svg)
        )

def quiz_list_w2py(): #lti=lti):  # Flask param - use on web2py??
    # Required for cookies to work in LTI land
    session.samesite('none')

    #response.view = 'generic.json'
    ret = dict()

    return_url = request.vars.get("launch_presentation_return_url", None)
    if return_url is None:
        # Try loading from the session.
        return_url = session.get("return_url", "#")
    session.return_url = return_url
    

    # Check oauth to make sure anon users don't hit the service
    # from pylti.flask import lti  Add decorator
    # @lti(request='initial', error=error, app=app)
    # Has PYLTI_CONFIG { "consumers": { os.environ.get("CONSUMER_KEY", "CHANGEME"): { "secret": os.environ.get("LTI_SECRET", "CHANGEME")}}}

    new_quiz_button = ""
    links = list()

    if session.is_teacher or session.is_admin:
        # new_quiz_button = SQLFORM.factory(
        #     submit_button="+ New Quiz",
        #     _name="new_quiz_button"
        # ).process(formname="new_quiz_button")

        # if new_quiz_button.accepted:
        #     redirect(URL('create_quiz'))
        #     return
    
        links.append(
            (dict(header=T(''), body=lambda row: (
                A('Edit', _class='ui button mini', _style2='font-size: 10px; color: red;', _href=URL('lti', 'edit_quiz', args=[row.id], user_signature=True)),
                A('Delete', _class='ui red button mini', _style2='font-size: 10px; color: red;', _href=URL('lti', 'delete_quiz', args=[row.id], user_signature=True)),
            )))
        )
   

    quiz_list = SQLFORM.grid(
        db_lti.ope_quizzes,
        fields=[
            db_lti.ope_quizzes.title,
            db_lti.ope_quizzes.description,
        ],
        orderby=[db_lti.ope_quizzes.quiz_position, db_lti.ope_quizzes.title.lower()],
        paginate=60,
        deletable=False,
        editable=False,
        details=False,
        create=False,
        csv=False,
        maxtextlength=150,
        links=links,
    )

    ret["vars"] = "<pre>" + json.dumps(request.vars, indent=4) + "</pre>"
    ret["quiz_list"] = quiz_list
    ret["new_quiz_button"] = new_quiz_button
        
    return ret

def edit_quiz():
    ret = dict()

    quiz_id = request.args(0)
    if quiz_id is None:
        print(f"Error - trying to edit None quiz id.")
        redirect(URL('lti', 'quizzes'))
        return None

    if session.is_admin or session.is_teacher:
        # Only grab quiz if it is from the current course.
        quiz_query = (
            (db_lti.ope_quizzes.lms_parent_course==session.lti.get("custom_canvas_course_id", -1)) &
            (db_lti.ope_quizzes.id==quiz_id)
        )
        quiz_item = db_lti(quiz_query).select().first()
        if quiz_item is None:
            print(f"Error - trying to edit invalid quiz {quiz_id}")
            redirect(URL('lti', 'quizzes'))
            return None


        # If form submitted, save changes.
        if request.vars.id:
            # Make sure UUID matches
            curr_uuid = get_form_uuid()
            new_uuid = request.vars.FORM_UUID
            if curr_uuid == new_uuid:
                #print(f"SUBMITTED {request.vars}")
                title = request.vars.title
                description = request.vars.description
                quiz_type = request.vars.quiz_type
                available_on_offline_laptop = request.vars.available_on_offline_laptop
                shuffle_answers = request.vars.shuffle_answers
                time_limit_enabled = request.vars.time_limit_enabled
                time_limit = request.vars.time_limit
                allow_multiple_attempts = request.vars.allow_multiple_attempts
                allowed_attempts = request.vars.allowed_attempts
                scoring_policy = request.vars.scoring_policy
                never_hide_results = request.vars.never_hide_results
                hide_results_only_after_last = request.vars.hide_results_only_after_last
                one_time_results = request.vars.one_time_results
                show_correct_answers = request.vars.show_correct_answers
                show_correct_answers_last_attempt = request.vars.show_correct_answers_last_attempt
                show_correct_answers_at = request.vars.show_correct_answers_at
                hide_correct_answers_at = request.vars.hide_correct_answers_at
                one_question_at_a_time = request.vars.one_question_at_a_time
                cant_go_back = request.vars.cant_go_back
                enable_quiz_access_code = request.vars.enable_quiz_access_code
                access_code = request.vars.access_code
                enable_quiz_ip_filter = request.vars.enable_quiz_ip_filter
                ip_filter = request.vars.ip_filter

                from dateutil.parser import parse as dateparse
                # Convert date/time values to proper format
                if show_correct_answers_at != '':
                    show_correct_answers_at = dateparse(show_correct_answers_at)
                if hide_correct_answers_at != '':
                    hide_correct_answers_at = dateparse(hide_correct_answers_at)


                r = db_lti(quiz_query).validate_and_update(
                    title=title,
                    description=description,
                    quiz_type = quiz_type,
                    available_on_offline_laptop = available_on_offline_laptop,
                    shuffle_answers = shuffle_answers,
                    time_limit_enabled = time_limit_enabled,
                    time_limit = time_limit,
                    allow_multiple_attempts = allow_multiple_attempts,
                    allowed_attempts = allowed_attempts,
                    scoring_policy = scoring_policy,
                    never_hide_results = never_hide_results,
                    hide_results_only_after_last = hide_results_only_after_last,
                    one_time_results = one_time_results,
                    show_correct_answers = show_correct_answers,
                    show_correct_answers_last_attempt = show_correct_answers_last_attempt,
                    show_correct_answers_at = show_correct_answers_at,
                    hide_correct_answers_at = hide_correct_answers_at,
                    one_question_at_a_time = one_question_at_a_time,
                    cant_go_back = cant_go_back,
                    enable_quiz_access_code = enable_quiz_access_code,
                    access_code = access_code,
                    enable_quiz_ip_filter = enable_quiz_ip_filter,
                    ip_filter = ip_filter,

                )
                # len(r.errors) should be 0 if no errors.
                if len(r.errors.keys()) > 0:
                    msg = f"VALIDATION ERRORS: {r.errors}"
                    print(msg)
                    response.flash = msg
                    db_lti.rollback()
                else:
                    db_lti.commit()

                    # Re-select updated data from the database
                    quiz_item = db_lti(quiz_query).select().first()
                
            else:
                # Invalid UUID - bot??
                print(f"FORM UUID ERROR - IDs didn't match!")
                response.flash=f"FORM UUID ERROR - IDs didn't match!"
                redirect(URL('lti', 'quizzes'))
                return None
        #print(f"{quiz_item.as_dict()}")
        #ret['quiz_title'] = quiz_item.title
        ret = quiz_item.as_dict()      
    else:
        # Go away - if not a teacher, don't show anything!
        redirect(URL('lti', 'quizzes'))
        return None

    # Generate a new UUID
    FORM_UUID = get_form_uuid(force_new=True)
    ret["FORM_UUID"] = FORM_UUID

    return ret

def create_quiz():
    ret = dict()

    if session.is_admin == False and session.is_teacher == False:
        # Not an admin or teacher, get out!
        print(f"Student or anon user tried to access admin LTI functions!\n{session}")
        redirect(URL('quiz_list'))

    #print(f"Form: {request.vars}")
    if request.vars.quiz_title:
        # Make sure UUID matches
        curr_uuid = get_form_uuid()
        new_uuid = request.vars.FORM_UUID
        if curr_uuid == new_uuid:
            
            #print(f"{request.vars}")
            quiz_title = request.vars.get('quiz_title', '')
            quiz_description = request.vars.get('quiz_description', '')
            quiz_type = request.vars.get('quiz_type', 'assignment')
            available_on_offline_laptop = request.vars.get('available_on_offline_laptop', "off")
            if available_on_offline_laptop == "on":
                available_on_offline_laptop = True
            else:
                available_on_offline_laptop = False

            lms_parent_course = session.lti.get("custom_canvas_course_id", "-1")
            

            if quiz_type == "" or quiz_type == "" or lms_parent_course == "-1":
                response.flash="Incomplete, quiz not inserted!"
                return ret

            r = db_lti.ope_quizzes.insert(
                title=quiz_title,
                description=quiz_description,
                quiz_type=quiz_type,
                lms_parent_course=lms_parent_course,
                available_on_offline_laptop = available_on_offline_laptop
            )
            db_lti.commit()

            # New quiz created, send back to the quiz list
            response.flash="Quiz Created."
            redirect(URL('lti', 'quiz_list'))

        else:
                # Invalid UUID - bot??
                print(f"FORM UUID ERROR - IDs didn't match!")
                response.flash=f"FORM UUID ERROR - IDs didn't match!"
                redirect(URL('lti', 'quizzes'))
                return None
        
    # Generate a new UUID
    FORM_UUID = get_form_uuid(force_new=True)
    ret["FORM_UUID"] = FORM_UUID

    return ret


def get_form_uuid(key=None, force_new=False):
    """
    get_form_uuid

    Create a unique uuid for this form. Should be unique for each session + form/url
    """
    import uuid

    if not session.form_uuids:
        session.form_uuids = dict()
    
    form_uuid = None

    if key is None:
        key = request.env.web2py_original_uri
    
    if key in session.form_uuids:
        form_uuid = session.form_uuids[key]

    if form_uuid is None or force_new:
        form_uuid = str(uuid.uuid4()).replace("-", "")
    #print(f"FormUUID - {key} -> {form_uuid}")
    session.form_uuids[key] = form_uuid
    return form_uuid
