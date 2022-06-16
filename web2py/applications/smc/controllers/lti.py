import json
from gluon import current

from ednet.canvas import Canvas


# Help shut up pylance warnings
if 1 == 2:
      Field = Field
      cache = cache
      db = db
      db_lti = db_lti
      DAL = DAL
      IS_IN_SET = IS_IN_SET
      IS_IN_DB = IS_IN_DB
      auth = auth
      IS_NOT_EMPTY = IS_NOT_EMPTY
      response = response
      request = request
      session = session
      IMG = IMG
      URL = URL
      HTTP = HTTP
      A = A
      TABLE = TABLE
      TR = TR
      TD = TD
      SQLFORM = SQLFORM
      LABEL = LABEL
      redirect = redirect
      getMediaThumb = getMediaThumb
      getDocumentThumb = getDocumentThumb
      XML = XML
      T = T
      BUTTON = BUTTON


lti_settings = {
    "https://canvas.corrections.homeip.net": {
        "client_id": "OPE_LTI",
        "auth_login_url": "http://canvas.docker/api/lti/authorize_redirect",
        "auth_token_url": "http://canvas.docker/login/oauth2/token",
        "key_set_url": "http://canvas.docker/api/lti/security/jwks",
        "key_set": None,
        "private_key_file": "private.key",
        "deployment_ids": ["OPELTI_Deployment_ID"],
    }
}

@auth.requires_membership("Administrators")
def add_lti_tools_to_canvas():
    #response.view = 'generic.json'
    # Hit canvas and install the tools that are available in the SMC.
    ret = dict()
    lti_response = dict()
    lti_logs = list()

    from ednet.canvas import Canvas
    Canvas.Connect()

    smc_host = URL('', host=True)

    had_errors = False


    # List of tools.
    lti_tools = {
        "rce_insert_media": {
            "name": "OPE LTI - Insert SMC Media",
            "privacy_level": "public",
            "consumer_key": "OPE_LTI_Insert_SMC_Media",
            "shared_secret": "OPE_LTI_Insert_SMC_Media_SECREThkuts",
            "description": "Embed media directly from the SMC website.",
            "url": URL('lti', 'rce_insert_media', host=True),
            #"domain": URL('', host=True),
            "icon_url": URL('static', 'images/rce_media.png', host=True),
            "text": "Embed SMC Media File",
            #"custom_fields": [],
            "editor_button[url]": URL('lti', 'rce_insert_media', host=True),
            "editor_button[enabled]": True,
            "editor_button[icon_url]": URL('static', 'images/rce_media.png', host=True),
            "editor_button[selection_width]": "700",
            "editor_button[selection_height]": "600",
            "is_rce_favorite": True,
            #"editor_button[message_type]": "ContentItemSelectionRequest",
        },

        "ope_quizzes": {
            "name": "OPE LTI - OPE Quizzes",
            "privacy_level": "public",
            "consumer_key": "OPE_LTI_OPE_Quizzes",
            "shared_secret": "OPE_LTI_OPE_Quizzes_SECRETkgjhfdsfS",
            "description": "OPE Quiz Engine - Create and edit quizzes that can be delivered in the classroom or on offline laptops.",
            "url": URL('lti', "quizzes", host=True),
            "icon_url": URL('static', 'images/favicon.png', host=True),
            "text": "OPE - Quizzes",
            "course_navigation[enabled]": True,
            "course_navigation[text]": "OPE - Quizzes",
            "course_navigation[visibility]": "members",
            "course_navigation[windotTarget]": "_self",
            "course_navigation[default]": "enabled",
            "course_navigation[display_type]": "default",
            "oauth_compliant": True,
            "custom_fields[section_ids]" : '$Canvas.course.sectionIds', #'$Canvas.course.sectionSisSourceIds',  # comma list of database IDs enrolled in
            "custom_fields[section_sourced_id]" : '$CourseSection.sourcedId',
            "custom_fields[term_name]": '$Canvas.term.name',
            #"custom_fields[term_id]": '$Canvas.term.id',
            "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
            "custom_fields[membership_roles]": '$Canvas.membership.roles',
            "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        },

    }

    # Remove old versions of these tools.
    old_tools = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools")
    for tool in old_tools:
        if not "name" in tool:
            continue
        if tool["name"].startswith("OPE LTI"):
            # Remove it - we will re-add it below.
            l = f"Removing OLD OPE LTI tool: {tool['name']} - {tool['id']}..."
            print(l)
            lti_logs.append(l)
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/{tool['id']}",
                            method="DELETE", params=None)
            lti_response[f"DELETE {tool}"] = r

    
    for tool in lti_tools:
        item = lti_tools[tool]
        l = f"Adding OPE LTI Tool: {item['name']}..."
        print(l)
        lti_logs.append(l)
        r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools",
                            method="POST", params=item)
        if "is_rce_favorite" in item:
            # Need to tell canvas to mark this as an RCE favorite
            l = f"\tAdding OPE LTI Tool to RCE toolbar..."
            print(l)
            lti_logs.append(l)

            Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/rce_favorites/{r['id']}",
                            method="POST", params=None)
        lti_response["tool"] = r
    
    ret["lti_response"] = json.dumps(lti_response, indent=4)
    ret["lti_msg"] = "COMPLETE - LTI Tools should be present in the canvas instance now."
    ret["lti_logs"] = '\n'.join(lti_logs)

    return ret



def generate_lti_keys():
    # https://github.com/dmitry-viskov/pylti1.3/wiki/How-to-generate-JWT-RS256-key-and-JWKS
    from Crypto.PublicKey import RSA
    key = RSA.generate(4096)
    private_key = key.exportKey()
    public_key = key.publickey().exportKey()


    from jwcrypto.jwk import JWK
    
    jwk_obj = JWK.from_pem(public_key.encode('utf-8'))
    public_jwk = json.lads(jwk_obj.export_public())
    public_jwk['alg'] = 'RS256'
    public_jwk['use'] = 'sig'
    public_jwk_str = json.dumps(public_jwk)


    return

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
            _href=f"{return_url}?return_type=iframe&title={row.title}&width=650&height=405&url=" + URL('media', 'view_document', args=[row.document_guid], host=True)))
        )
    )
    links.append(dict(header=T(''), body=lambda row: A(TABLE(TR(
                                                TD(IMG(_src=getDocumentThumb(row.document_guid), _style="width: 24px;"),
                                                   _width=26),
                                                TD(LABEL(row.title), _align="left")
                                                )),
                                                _href=URL('media', 'view_document', args=[row.document_guid],
                                                user_signature=True))))
    fields = [db.document_files.id, db.document_files.title, db.document_files.tags, db.document_files.description,
              db.document_files.document_guid, db.document_files.category]  # [db.document_files.title]
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
    

    # rows = db(query).select()
    document_grid = SQLFORM.grid(query, editable=False, create=False, deletable=False,
                              csv=False, details=False,
                              searchable=True, orderby=[~db.document_files.modified_on],
                              fields=fields, paginate=15,
                              links=links, links_placement='left', links_in_grid=True,
                              maxtextlengths=maxtextlengths)

    return dict(document_grid=document_grid)

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
    # Required for cookies to work in LTI land
    session.samesite('none')

    #response.view = 'generic.json'
    ret = dict()

    # return_url = request.vars.get("launch_presentation_return_url", None)
    # if return_url is None:
    #     # Try loading from the session.
    #     return_url = session.get("return_url", "#")
    # session.return_url = return_url

    # Check oauth to make sure anon users don't hit the service
    # from pylti.flask import lti  Add decorator
    # @lti(request='initial', error=error, app=app)
    # Has PYLTI_CONFIG { "consumers": { os.environ.get("CONSUMER_KEY", "CHANGEME"): { "secret": os.environ.get("LTI_SECRET", "CHANGEME")}}}

    lti = dict()
    lti['lti_message_type'] = request.vars.get("lti_message_type", None) # should be basic-lti-launch-request
    lti['lti_version'] = request.vars.get('lti_version', None) # should be LTI-1p0
    lti['resource_link_id'] = request.vars.get('resource_link_id', None) # Unique ID for unique launch
    lti['user_id'] = request.vars.get("user_id", None)
    lti['user_image'] = request.vars.get("user_image", None) # Avatar if available
    lti['roles'] = request.vars.get('roles', list()) # List of roles - Learner, Instructor, ContentDeveloper, urn:lti:instrole:ims/lis/Observer, urn:lti:instrole:ims/lis/Administrator
    lti['lis_person_name_full'] = request.vars.get('lis_person_name_full', "")
    lti['lis_outcome_service_url'] = request.vars.get('lis_outcome_service_url', None)  # Where to send grades back for an assignment
    lti['selection_directive'] = request.vars.get('selection_directive', None) # If present - canvas is expecting a piece of information (url, html snippet, etc...) back

    # Common Parameters
    lti['lis_person_sourceid'] = request.vars.get('lis_person_sourceid', None) # username (e.g. s777777)
    lti['lis_person_name_given'] = request.vars.get('lis_person_name_given', None) # First name
    lti['lis_person_name_family'] = request.vars.get('lis_person_name_family', None) # Last name
    lti['lis_person_contact_email_primary'] = request.vars.get('lis_person_contact_email_primary', None)
    lti['resource_link_title'] = request.vars.get('resource_link_title', None) # Name of link that launched the app
    lti['resource_link_description'] = request.vars.get('resource_link_description', None) # Desc of the link that launched the app
    lti['context_id'] = request.vars.get('context_id', None) # unique id of the course (e.g. canvas course id)
    lti['context_type'] = request.vars.get('context_type', None) # context - prob CourseSection
    lti['context_title'] = request.vars.get('context_title', None) # Name of course 
    lti['context_label'] = request.vars.get('context_label', None) # Short name or course code

    lti['launch_presentation_locale'] = request.vars.get('launch_presentation_locale', 'en-US')
    lti['launch_presentation_document_target'] = request.vars.get('launch_presentation_document_target', None) # iframe or new window name to launch in
    lti['launch_presentation_css_url'] = request.vars.get('launch_presentation_css_url', None) # CSS doc to include to match display - can ignore
    lti['launch_presentation_width'] = request.vars.get('launch_presentation_width', '800') # width of window when launched
    lti['launch_presentation_height'] = request.vars.get('launch_presentation_height', '700') # height of window when launched
    lti['launch_presentation_return_url'] = request.vars.get('launch_presentation_return_url', None) # url to send user to when finished. Can also send the following as parameters
    # lti_errormsg, lti_errorlog (store without showing to user?), lti_msg (success message), lti_log (success, store w/out showing to user)

    lti['tool_consumer_info_product_family_code'] = request.vars.get('tool_consumer_info_product_family_code', None) # product name: e.g. moodle, sakai, canvas
    lti['tool_consumer_info_version'] = request.vars.get('tool_consumer_info_version', None) # version number of canvas
    lti['tool_consumer_instance_guid'] = request.vars.get('tool_consumer_instance_guid', None) # unique id for the canvas instance (e.g. current school in canvas?)
    lti['tool_consumer_instance_name'] = request.vars.get('tool_consumer_instance_name', None) # name of instance (e.g. Open Prison Education)
    lti['tool_consumer_instance_description'] = request.vars.get('tool_consumer_instance_description', None) 
    lti['tool_consumer_instance_url'] = request.vars.get('tool_consumer_instance_url', None) # The url of the instance of canvas
    lti['tool_consumer_instance_contact_email'] = request.vars.get('tool_consumer_instance_contact_email', None) # admin contact email

    #lti['custom_*'] = Custom fields sent
    lti['custom_canvas_user_id'] = request.vars.get('custom_canvas_user_id', None) # The database ID for the user (e.g. 49800000002)
    lti['custom_canvas_login_id'] = request.vars.get('custom_canvas_login_id', None) # The login id: s777777
    lti['custom_canvas_course_id'] = request.vars.get('custom_canvas_course_id', None) # The database ID for the course (e.g. 4980000012)
    lti['custom_canvas_workflow_state'] = request.vars.get('custom_canvas_workflow_state', None) # available
    lti['custom_canvas_enrollment_state'] = request.vars.get('custom_canvas_enrollment_state', None) # active

    lti['custom_canvas_api_domain'] = request.vars.get('custom_canvas_api_domain', None) # canvas.ed (host name of server)



    # OAuth params
    lti['oauth_nonce'] = request.vars.get('oauth_nonce', None)
    lti['oauth_signature'] = request.vars.get('oauth_signature', None)
    lti['oauth_version'] = request.vars.get('oauth_version', None)
    lti['oauth_signature_method'] = request.vars.get('oauth_signature_method', None) # 'HMAC-SHA1'
    lti['oauth_consumer_key'] = request.vars.get('oauth_consumer_key', None)    # Something like 'OPE_LTI_OPE_Quizzes'






    """
    LTI Params: {
        'lti_message_type': 'basic-lti-launch-request',
        'lti_version': 'LTI-1p0',
        'resource_link_id': 'ef2abfbc5be7293b12dc24b828b3fa2a27552f26',
        'user_id': '8b34d662610c65a5abecdd3e34a60756d27658c5',
        'user_image': 'https://canvas.corrections.homeip.net/images/messages/avatar-50.png',
        'roles': 'Instructor,urn:lti:instrole:ims/lis/Administrator,urn:lti:sysrole:ims/lis/SysAdmin',
        'lis_person_name_full': 'admin@corrections.homeip.net',
        'lis_outcome_service_url': None,
        'selection_directive': None,
        'lis_person_name_given': 'admin@corrections.homeip.net',
        'lis_person_name_family': '',
        'lis_person_contact_email_primary': 'admin@corrections.homeip.net',
        'resource_link_title': 'OPE LTI - OPE Quizzes',
        'resource_link_description': None,
        'context_id': 'ef2abfbc5be7293b12dc24b828b3fa2a27552f26',
        'context_type': None,
        'context_title': 'TEST_COURSE',
        'context_label': 'TEST_COURSE',
        'launch_presentation_locale': 'en',
        'launch_presentation_document_target': 'iframe',
        'launch_presentation_css_url': None,
        'launch_presentation_width': '800',
        'launch_presentation_height': '400',
        'launch_presentation_return_url': 'https://canvas.corrections.homeip.net/courses/345810000004092/external_content/success/external_tool_redirect',
        'tool_consumer_info_product_family_code': 'canvas',
        'tool_consumer_info_version': 'cloud',
        'tool_consumer_instance_guid': 'jJ2u6lI5Qo8CoCCTSUn5koI1MQXnSfI0EaiYFKcy:canvas-lms',
        'tool_consumer_instance_name': 'Open Prison Education',
        'tool_consumer_instance_description': None,
        'tool_consumer_instance_url': None,
        'tool_consumer_instance_contact_email': 'admin@corrections.homeip.net'
    }
"""

    # Canvas public jwks keys at: /api/lti/security/jwks

    print(f"LTI Params: {lti}")
    print(f"Raw Params: {request.vars}")

    error_string = ""

    if lti['lti_message_type'] != 'basic-lti-launch-request':
        error_string += "Invalid LTI Message Type"
    
    if lti['lti_version'] != 'LTI-1p0':
        error_string += "Invalid LTI Version"

    

    if len(error_string) > 1:
        request.view = 'generic.json'
        return error_string

 
    session.current_lti_params = lti
    session.return_url = lti["launch_presentation_return_url"]
    session.is_teacher = False
    session.is_student = False
    session.is_admin = False

    if 'Learner' in lti['roles']:
        print("LTI - Is student")
        session.is_student = True
    
    if 'Instructor' in lti['roles']:
        print("LTI - Is teacher")
        session.is_teacher = True
    
    if 'urn:lti:instrole:ims/lis/Administrator' in lti['roles'] or 'urn:lti:sysrole:ims/lis/SysAdmin' in lti['roles']:
        print("LTI - Is admin")
        session.is_admin = True

    redirect(URL('quiz_list'))


def quiz_list(): #lti=lti):  # Flask param - use on web2py??
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
        new_quiz_button = SQLFORM.factory(
            submit_button="+ New Quiz",
            _name="new_quiz_button"
        ).process(formname="new_quiz_button")

        if new_quiz_button.accepted:
            redirect(URL('create_quiz'))
            return
    
        links.append(
            (dict(header=T(''), body=lambda row: (
                A('[Edit]', _style='font-size: 10px; color: red;', _href=URL('lti', 'edit_quiz', args=[row.id], user_signature=True)),
                " | ",
                A('[Delete]', _style='font-size: 10px; color: red;', _href=URL('lti', 'delete_quiz', args=[row.id], user_signature=True)),
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

def create_quiz():
    ret = dict()

    if session.is_admin == False and session.is_teacher == False:
        # Not an admin or teacher, get out!
        print(f"Student or anon user tried to access admin LTI functions!\n{session}")
        redirect(URL('quiz_list'))

    quiz_create_form = SQLFORM(
        db_lti.ope_quizzes,
        fields=['title', 'description', 'quiz_type'],
        submit_button="Create Quiz", 
        _name="quiz_create_form",
        buttons = [BUTTON('Cancel', _class="btn btn-primary", _type="button", _onClick="window.location='%s'" % URL("quiz_list")),
                   BUTTON('Create Quiz', _class="btn btn-primary", _type="submit")],  #btn btn-primary
    ).process(formname="quiz_create_form")

    if quiz_create_form.accepted:
        # Add the new quiz
        #print(f"Created Quiz: {quiz_create_form.vars.title}")
        redirect(URL('quiz_list'))
        pass

    ret["quiz_create_form"] = quiz_create_form

    return ret