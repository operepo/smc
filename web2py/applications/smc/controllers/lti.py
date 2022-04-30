import json
from gluon import current

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



def install_lti_tools():
    response.view = 'generic.json'
    # Hit canvas and install the tools that are available in the SMC.
    ret = dict()

    from ednet.canvas import Canvas
    Canvas.Connect()

    smc_host = URL('', host=True)


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
            "test": "OPE Quizzes",
            "course_navigation[enabled]": True,
            "course_navigation[text]": "OPE Quizzes",
            "course_navigation[visibility]": "public",
            "course_navigation[windotTarget]": "_self",
            "course_navigation[default]": "enabled",
            "course_navigation[display_type]": "default",
            "oauth_compliant": True,
        },
    }

    # Remove old versions of these tools.
    old_tools = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools")
    for tool in old_tools:
        if not "name" in tool:
            continue
        if tool["name"].startswith("OPE LTI"):
            # Remove it - we will re-add it below.
            print(f"Removing OLD OPE LTI tool: {tool['name']} - {tool['id']}...")
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/{tool['id']}",
                            method="DELETE", params=None)
            ret[f"DELETE {tool}"] = r

    
    for tool in lti_tools:
        item = lti_tools[tool]
        print(f"Adding OPE LTI Tool: {item['name']}...")
        r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools",
                            method="POST", params=item)
        if "is_rce_favorite" in item:
            # Need to tell canvas to mark this as an RCE favorite
            print(f"\tAdding OPE LTI Tool to RCE toolbar...")

            Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/rce_favorites/{r['id']}",
                            method="POST", params=None)
        ret["tool"] = r

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


# Quizzes interface for students or admin users.
def quizzes(): #lti=lti):  # Flask param - use on web2py??
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

    new_quiz_button = SQLFORM.factory(
        submit_button="+ New Quiz",
        _name="new_quiz_button"
    ).process(formname="new_quiz_button")

    if new_quiz_button.accepted:
        redirect(URL('create_quiz'))
        return
    
    quiz_list = SQLFORM.grid(
        db.ope_quizzes,
        fields=[
            db.ope_quizzes.title,
            db.ope_quizzes.description,
        ],
        orderby=[db.ope_quizzes.title.lower()],
        paginate=40,
        deletable=False,
        editable=True,
        details=False,
        create=False,
        csv=False,
        maxtextlength=50,
        #links=None        
    )

    ret["vars"] = "<pre>" + json.dumps(request.vars, indent=4) + "</pre>"
    ret["quiz_list"] = quiz_list
    ret["new_quiz_button"] = new_quiz_button
        
    return ret

def create_quiz():
    ret = dict()

    quiz_create_form = SQLFORM(
        db.ope_quizzes,
        fields=['title', 'description', 'quiz_type', 'points_possible'],
        submit_button="Create Quiz",
        _name="quiz_create_form"
    ).process(formname="quiz_create_form")

    if quiz_create_form.accepted:
        # Add the new quiz
        #print(f"Created Quiz: {quiz_create_form.vars.title}")
        redirect(URL('quizzes'))
        pass

    ret["quiz_create_form"] = quiz_create_form

    return ret