# -*- coding: utf-8 -*-

### Chunk Management - Allow posting, getting, or querying of a data chunk
###
###
###

from gluon.tools import Service
service = Service()

# Call this to get RPC object
def call():
    session.forget()
    return service()


@service.json
@service.jsonrpc
@service.jsonrpc2
def get_chunk(user_id, auth_key, chunk_id):
    ret = dict(status="", chunk_data=None, chunk_id=chunk_id, err="")
    
    # Validate auth - Are they a real user and are they logged in?
    if not validate_user(user_id, auth_key):
        ret['err'] = "Invalid User!"
        ret['status'] = "ERROR"
        return ret

    # Load the chunk and return it
    chunk = Chunk(chunk_id)
    if not chunk.authorize(user_id):
        # User not allowed to grab this chunk!
        ret['err'] = "Not authorized!"
        ret['status'] = "ERROR"
        return ret
    
    # Is chunk a valid chunk?
    if not chunk.validate():
        # Error validating this chunk! It is wrong? Doesn't decrypt? Doesn't pass hash check?
        ret['status'] = "ERROR"
        ret['err'] = "Invalid Chunk!"
        return ret
    
    # Chunk should be good, return it
    ret['status'] = "OK"
    ret['chunk_data'] = chunk.data

    return ret


@service.json
@service.jsonrpc
@service.jsonrpc2
def put_chunk(user_id, auth_key, chunk_id, chunk_data):
    # Save a chunk to the server
    ret = dict(status="", chunk_data=None, chunk_id=chunk_id, err="")

    # Validate auth - Are they a real user and are they logged in?
    if not validate_user(user_id, auth_key):
        ret['err'] = "Invalid User!"
        ret['status'] = "ERROR"
        return ret
    
    # Load the chunk (if it exists)
    chunk = Chunk(chunk_id)

    # Set the data
    self.chunk_data = chunk_data

    # Is chunk a valid chunk?
    if not chunk.validate():
        # Error validating this chunk! It is wrong? Doesn't decrypt? Doesn't pass hash check?
        ret['status'] = "ERROR"
        ret['err'] = "Invalid Chunk!"
        return ret
    
    # Add this user to the list on this chunk
    chunk.add_user(user_id)

    # Save the chunk to the disk
    chunk.save()

    ret["status"] = "OK"

    return ret


@service.json
@service.jsonrpc
@service.jsonrpc2
def query_chunk(user_id, auth_key, chunk_id):
    # Get chunk info
    ret = dict(status="", chunk_data=None, chunk_id=chunk_id, err="")

    # Validate auth - Are they a real user and are they logged in?
    if not validate_user(user_id, auth_key):
        ret['err'] = "Invalid User!"
        ret['status'] = "ERROR"
        return ret

    # Load the chunk and return it
    chunk_exists = Chunk.query(chunk_id)
        
    # Chunk should be good, return it
    ret['status'] = "OK"
    ret['chunk_data'] = None

    return ret








