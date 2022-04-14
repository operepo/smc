#from pylti1p3.tool_config import ToolConfJsonFile
#tool_conf = ToolConfJsonFile('path/to/json')
from pylti1p3.tool_config import ToolConfDict
settings = {
    "iss1": [
        {
            "default": True,
            "client_id": "client_id1",  # Recieved from canvas in aud
            "auth_login_url": "",
            "auth_token_url": "",
            "auth_audience": None,
            "key_set_url": "",
            "key_set": None,
            "private_key_file": "private.key",
            "public_key_file": "public.key",
            "deployment_ids": ["id1", "id2"],
        }
    ],
}
private_key = '...'
public_key = '...'
tool_conf = ToolConfDict(settings)

client_id = '...'
tool_conf.set_private_key(iss, private_key, client_id=client_id)
tool_conf.set_public_key(iss, public_key, client_id=client_id)

import json
from gluon import current


# Fetch quiz questions and pack them up into an encrypted package
def student_quizzes():
    response.view = 'generic.json'
    ret = dict()
    ret['Hello World']
    
    
    return json.dumps(ret)