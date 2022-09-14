
# LTI Library code

import os
import json

from ednet.appsettings import AppSettings
from ednet.canvas import Canvas

# Help shut up pylance warnings
if 1==2: from ..common import *

def init_lti(force=False):
    # Required for cookies to work in LTI land
    session.samesite('none')

    if session.get('init_lti', False) == True and force == False:
        # LTI has already been init, don't redo all of this.
        return session.is_lti

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
    lti['custom_canvas_user_login_id'] = request.vars.get('custom_canvas_user_login_id', None) # The login id: s777777
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

 
    session.lti = lti
    session.canvas_course_id = lti["custom_canvas_course_id"]
    session.return_url = lti["launch_presentation_return_url"]
    session.is_lti = False
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

    if session.is_student or session.is_teacher or session.is_admin:
        session.is_lti = True

    return session.is_lti

def is_lti():
    if session.is_lti == True:
        return True
    return False

def is_lti_student():
    if session.is_student == True:
        return True
    return False

def is_lti_teacher():
    if session.is_teacher == True:
        return True
    return False

def is_lti_admin():
    if session.is_admin == True:
        return True
    return False


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

def install_lti_tools():
    ret = {
        "lti_response": "",
        "lti_msg":  "",
        "lti_logs": ""
    }
    lti_response = dict()
    lti_logs = list()

    
    if not Canvas.isEnabled() == True:
        print(f"Canvas not enabled, not installing LTI tools.")
        ret['lti_msg'] = "Canvas Integration Not Enabled!"
        return ret

    Canvas.Connect()

    # Running in scheduler - have to pull the "hostname" from the environment.
    scheme = "https"
    smc_host = os.environ.get('SMC_DEFAULT_DOMAIN', 'localhost:8000')

    had_errors = False

    # List of tools to remove (e.g. old tools that shouldn't be used anymore)
    # Just need the "consumer_key" of the tools.
    lti_remove_tools = [
        #"OPE_LTI_Deprecated_Tool"
    ]

    
    # List of tools.
    lti_tools = {
        "rce_insert_media": {
            "name": "OPE LTI - Insert SMC Media",
            "privacy_level": "public",
            "consumer_key": "OPE_LTI_Insert_SMC_Media",
            "shared_secret": "OPE_LTI_Insert_SMC_Media_SECREThkuts",
            "description": "Embed media directly from the SMC website.",
            "url": URL('lti', 'rce_insert_media', host=smc_host, scheme=scheme),
            #"domain": URL('', host=True),
            "icon_url": URL('static', 'images/rce_insert_media.png', host=smc_host, scheme=scheme),
            "text": "Embed SMC Media File",
            #"custom_fields": [],
            "editor_button[url]": URL('lti', 'rce_insert_media', host=smc_host, scheme=scheme),
            "editor_button[enabled]": True,
            "editor_button[icon_url]": URL('static', 'images/rce_insert_media.png', host=smc_host, scheme=scheme),
            "editor_button[selection_width]": "700",
            "editor_button[selection_height]": "600",
            "is_rce_favorite": True,
            #"editor_button[message_type]": "ContentItemSelectionRequest",
        },
        "rce_insert_document": {
            "name": "OPE LTI - Insert SMC Document",
            "privacy_level": "public",
            "consumer_key": "OPE_LTI_Insert_SMC_Document",
            "shared_secret": "OPE_LTI_Insert_SMC_Document_SECRETgoiskjh",
            "description": "Embed documents directly from the SMC website.",
            "url": URL('lti', 'rce_insert_document', host=smc_host, scheme=scheme),
            #"domain": URL('', host=True),
            "icon_url": URL('static', 'images/rce_insert_document.png', host=smc_host, scheme=scheme),
            "text": "Embed SMC Document File",
            #"custom_fields": [],
            "editor_button[url]": URL('lti', 'rce_insert_document', host=smc_host, scheme=scheme),
            "editor_button[enabled]": True,
            "editor_button[icon_url]": URL('static', 'images/rce_insert_document.png', host=smc_host, scheme=scheme),
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
            "url": URL('lti', "quizzes", host=smc_host, scheme=scheme),
            "icon_url": URL('static', 'images/favicon.png', host=smc_host, scheme=scheme),
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
            # Canvas doesn't support many of these
            #"custom_fields[section_label]": '$CourseSection.label',
            #"custom_fields[section_title]": '$CourseSection.title',
            #"custom_fields[section_short_description]": '$CourseSection.shortDescription',
            #"custom_fields[section_course_number]": '$CourseSection.courseNumber',
            #"custom_fields[section_data_source]": '$CourseSection.dataSource',
            #"custom_fields[section_section_id]": '$CourseSection.sourceSectionId',
            "custom_fields[term_name]": '$Canvas.term.name',
            #"custom_fields[term_id]": '$Canvas.term.id',
            "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
            "custom_fields[membership_roles]": '$Canvas.membership.roles',
            "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        },

        "ope_help_portal": {
            "name": "OPE LTI - OPE Help Portal",
            "privacy_level": "public",
            "consumer_key": "OPE_LTI_OPE_help_portal",
            "shared_secret": "OPE_LTI_OPE_Help_Portal_SECRETkgjhfdsfS",
            "description": "OPE Help Portal - Help resources for Students, Faculty, and Administrators.",
            "url": URL('help_portal', "index", host=smc_host, scheme=scheme),
            "icon_url": URL('static', 'images/lti_global_help_icon.png', host=smc_host, scheme=scheme),
            "text": "OPE - Help Portal",
            "course_navigation[enabled]": False,
            "global_navigation[enabled]": True,
            "global_navigation[text]": "OPE Help Portal",
            "global_navigation[visibility]": "members",
            "global_navigation[windotTarget]": "_self",
            "global_navigation[default]": "enabled",
            "global_navigation[display_type]": "default",
            "oauth_compliant": True,
            "custom_fields[section_ids]" : '$Canvas.course.sectionIds', #'$Canvas.course.sectionSisSourceIds',  # comma list of database IDs enrolled in
            "custom_fields[section_sourced_id]" : '$CourseSection.sourcedId',
            "custom_fields[term_name]": '$Canvas.term.name',
            #"custom_fields[term_id]": '$Canvas.term.id',
            "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
            "custom_fields[membership_roles]": '$Canvas.membership.roles',
            "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        },

        # "ope_student_help": {
        #     "name": "OPE LTI - OPE Student Help",
        #     "privacy_level": "public",
        #     "consumer_key": "OPE_LTI_OPE_student_help",
        #     "shared_secret": "OPE_LTI_OPE_Student_Help_SECRETkgjhfdsfS",
        #     "description": "OPE Student Help Portal - Help resources for Students.",
        #     "url": URL('help_portal', "student", host=smc_host, scheme=scheme),
        #     "icon_url": URL('static', 'images/lti_global_help_icon.png', host=smc_host, scheme=scheme),
        #     "text": "OPE - Student Help",
        #     "course_navigation[enabled]": False,
        #     "global_navigation[enabled]": True,
        #     "global_navigation[text]": "Student Help",
        #     "global_navigation[visibility]": "members",
        #     "global_navigation[windotTarget]": "_self",
        #     "global_navigation[default]": "enabled",
        #     "global_navigation[display_type]": "default",
        #     "oauth_compliant": True,
        #     "custom_fields[section_ids]" : '$Canvas.course.sectionIds', #'$Canvas.course.sectionSisSourceIds',  # comma list of database IDs enrolled in
        #     "custom_fields[section_sourced_id]" : '$CourseSection.sourcedId',
        #     "custom_fields[term_name]": '$Canvas.term.name',
        #     #"custom_fields[term_id]": '$Canvas.term.id',
        #     "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
        #     "custom_fields[membership_roles]": '$Canvas.membership.roles',
        #     "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        # },

        # "ope_faculty_help": {
        #     "name": "OPE LTI - OPE Faculty Help",
        #     "privacy_level": "public",
        #     "consumer_key": "OPE_LTI_OPE_faculty_help",
        #     "shared_secret": "OPE_LTI_OPE_Faculty_Help_SECRETkgjhfdsfS",
        #     "description": "OPE Faculty Help Portal - Help resources for Faculty.",
        #     "url": URL('help_portal', "faculty", host=smc_host, scheme=scheme),
        #     "icon_url": URL('static', 'images/lti_global_help_icon.png', host=smc_host, scheme=scheme),
        #     "text": "OPE - Faculty Help",
        #     "course_navigation[enabled]": False,
        #     "global_navigation[enabled]": True,
        #     "global_navigation[text]": "Faculty Help",
        #     "global_navigation[visibility]": "admins",
        #     "global_navigation[windotTarget]": "_self",
        #     "global_navigation[default]": "enabled",
        #     "global_navigation[display_type]": "default",
        #     "oauth_compliant": True,
        #     "custom_fields[section_ids]" : '$Canvas.course.sectionIds', #'$Canvas.course.sectionSisSourceIds',  # comma list of database IDs enrolled in
        #     "custom_fields[section_sourced_id]" : '$CourseSection.sourcedId',
        #     "custom_fields[term_name]": '$Canvas.term.name',
        #     "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
        #     "custom_fields[membership_roles]": '$Canvas.membership.roles',
        #     "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        # },

        # "ope_it_help": {
        #     "name": "OPE LTI - OPE IT Help",
        #     "privacy_level": "public",
        #     "consumer_key": "OPE_LTI_OPE_it_help",
        #     "shared_secret": "OPE_LTI_OPE_it_Help_SECRETkgjhfdsfS",
        #     "description": "OPE IT Help Portal - Help resources for Admins.",
        #     "url": URL('help_portal', "it_support", host=smc_host, scheme=scheme),
        #     "icon_url": URL('static', 'images/lti_global_help_icon.png', host=smc_host, scheme=scheme),
        #     "text": "OPE - IT Help",
        #     "course_navigation[enabled]": False,
        #     "global_navigation[enabled]": True,
        #     "global_navigation[text]": "IT Help",
        #     "global_navigation[visibility]": "admins",
        #     "global_navigation[windotTarget]": "_self",
        #     "global_navigation[default]": "enabled",
        #     "global_navigation[display_type]": "default",
        #     "oauth_compliant": True,
        #     "custom_fields[section_ids]" : '$Canvas.course.sectionIds', #'$Canvas.course.sectionSisSourceIds',  # comma list of database IDs enrolled in
        #     "custom_fields[section_sourced_id]" : '$CourseSection.sourcedId',
        #     "custom_fields[term_name]": '$Canvas.term.name',
        #     "custom_fields[sis_section_ids]": '$Canvas.course.sectionSisSourceIds',
        #     "custom_fields[membership_roles]": '$Canvas.membership.roles',
        #     "custom_fields[section_name]": '$com.instructure.User.sectionNames',
        # },

# Example of deep linking?
        # "ope_rce": {
        #     "title": "OPE LTI - SMC Integration",
        #     "scopes": [],
        #     "extensions": [
        #         {
        #             "domain": URL('', host=smc_host, scheme=scheme),
        #             "tool_id": "ope-lti-smc",
        #             "platform": "canvas.instructure.com",
        #             "settings": {
        #                 "text": "OPE LTI Integration",
        #                 "icon_url": URL('static', 'images/favicon.png', host=smc_host, scheme=scheme),
        #                 "placements": [
        #                     {
        #                         "text": "Insert SMC Media",
        #                         "enabled": True,
        #                         "icon_url": URL('static', 'images/rce_insert_media.png', host=smc_host, scheme=scheme),
        #                         "placement": "editor_button",
        #                         "message_type": "LtiDeepLinkingRequest",
        #                         "target_link_uri": URL('lti', 'rce_insert_media', host=smc_host, scheme=scheme),

        #                     },
        #                     {
        #                         "text": "Insert SMC Document",
        #                         "enabled": True,
        #                         "icon_url": URL('static', 'images/document_file.png', host=smc_host, scheme=scheme),
        #                         "placement": "editor_button",
        #                         "message_type": "LtiDeepLinkingRequest",
        #                         "target_link_uri": URL('lti', 'rce_insert_document', host=smc_host, scheme=scheme),
        #                     },
        #                     {
        #                         "text": "OPE LTI Quiz Assignment",
        #                         "enabled": True,
        #                         "icon_url": URL('static', 'images/favicon.png', host=smc_host, scheme=scheme),
        #                         "placement": "assignment_selection",
        #                         "message_type": "LtiDeepLinkingRequest",
        #                         "target_link_uri": URL('lti', "quizzes", host=smc_host, scheme=scheme)
        #                     }
        #                 ]
        #             }
        #         },
        #     ],
        #     "public_jwk": {
        #         "kty": "RSA",
        #         "alg": "RS256",
        #         "e": "AQAB",
        #         "kid": "?????",
        #         "n": ".....",
        #         "use": "sig"
        #     },
        #     "description": "OPE LTI Tool - Integrating SMC tools into canvas.",
        #     "target_link_uri": URL('lti', host=True),
        #     "oidc_initiation_url": URL('lti', "oidc_initiation", host=True)
        # }

    }

    # Get the list of external tools so we can update them if found.
    current_tools = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools")
    
    # Remove old tools.
    for tool in lti_remove_tools:
        # Go through the current tools and remove the ones we don't want.

        for t in current_tools:
            if not "consumer_key" in t:
                continue
            if t["consumer_key"] == tool:
                # Remove it
                l = f"Removing OLD OPE LTI tool: {t['name']} - {t['id']}..."
                print(l)
                lti_logs.append(l)
                r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/{t['id']}",
                                method="DELETE", params=None)
                lti_response[f"DELETE {t['name']}"] = r

    # Refresh the list after deletes
    current_tools = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools")
    
    # Loop through our tools and create or update as needed.
    for tool in lti_tools:
        item = lti_tools[tool]

        # Check in the current tools to see if it is installed
        is_installed = False
        tool_id = None
        for t in current_tools:
            if not "consumer_key" in t:
                continue
            if t["consumer_key"] == item["consumer_key"]:
                # Found it.
                tool_id = t['id']
                is_installed = True
                break

        if is_installed == True:
            # Need to update existing tool
            l = f"Updating OPE LTI Tool: {item['name']}..."
            print(l)
            lti_logs.append(l)
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/{tool_id}",
                                method="PUT", params=item)
            if "is_rce_favorite" in item:
                # Need to tell canvas to mark this as an RCE favorite
                l = f"\t-> Adding to RCE toolbar {item['name']}..."
                print(l)
                lti_logs.append(l)

                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/rce_favorites/{tool_id}",
                                method="POST", params=None)
            lti_response[f"API Response: {item['name']}"] = r

        else:
            # Need to create new tool.
            l = f"Adding OPE LTI Tool: {item['name']}..."
            print(l)
            lti_logs.append(l)
            r = Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, "/api/v1/accounts/self/external_tools",
                                method="POST", params=item)
            if "is_rce_favorite" in item:
                # Need to tell canvas to mark this as an RCE favorite
                l = f"\t-> Adding to RCE toolbar {item['name']}..."
                print(l)
                lti_logs.append(l)

                Canvas.APICall(Canvas._canvas_server_url, Canvas._canvas_access_token, f"/api/v1/accounts/self/external_tools/rce_favorites/{r['id']}",
                                method="POST", params=None)
            lti_response[f"API Response: {item['name']}"] = r

    
    ret["lti_response"] = json.dumps(lti_response, indent=4)
    ret["lti_msg"] = "COMPLETE - LTI Tools should be present in the canvas instance now."
    ret["lti_logs"] = '\n'.join(lti_logs)


    return ret
