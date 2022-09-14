
# Help shut up pylance warnings
if 1==2: from ..common import *

def index():
    init_lti()
    return dict()

def faculty():
    init_lti()
    if not is_lti_teacher() and not is_lti_admin():
        # Show unauthorized error
        raise HTTP(401, "You do not have the proper permissions to access this resource.")
    return dict()


def student():
    init_lti()
    if not is_lti_student() and not is_lti_teacher() and not is_lti_admin():
        # Show unauthorized error
        raise HTTP(401, "You do not have the proper permissions to access this resource.")
    return dict()


def it_support():
    init_lti()
    if not is_lti_admin():
        # Show unauthorized error
        raise HTTP(401, "You do not have the proper permissions to access this resource.")
    return dict()
