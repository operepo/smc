

import ssl
# Do this so that we allow test certs w/o error
ssl._create_default_https_context = ssl._create_unverified_context

def test_chunks():
    response.view = 'generic.json'
    from gluon.contrib.simplejsonrpc import ServerProxy
    msg = "TEST"

    url = "https://127.0.0.1:8000/data_sync/chunk/call/jsonrpc"

    service = ServerProxy(url, verbose=True)

    chunk = service.get_chunk("user!", "key!", "chunk_id")
    return dict(msg=msg, chunk=chunk)
