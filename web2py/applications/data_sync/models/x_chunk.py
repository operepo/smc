
import os
import sys

class Chunk:
    default_chunk_drive = "drive0"

    def __init__(self, chunk_id=None):
        self.chunk_id = chunk_id
        self.users = dict()
        self.data = None
        self.drive = Chunk.default_chunk_drive
        self.load()
    
    def save(self):
        ret = False

        if not self.ensure_chunk_folder():
            return False
        
        return ret

    def load(self):
        # Load the chunk from the drive
        ret = False

        if not self.ensure_chunk_folder():
            return False

        # TODO TODO FINISH
        ret = True

        return ret
    
    def ensure_chunk_folder(self):
        # Make sure the chunk folder exists - for adding prefix folder
        chunks_folder = get_chunk_path()
        chunks_folder = os.path.join(chunks_folder, self.drive)

        prefix = self.chunk_id[:2]
        if len(prefix) < 2:
            return False
        
        chunks_folder = os.path.join(chunks_folder, prefix)
        # Make sure the folder exists
        os.makedirs(chunks_folder, exist_ok=True)
        self.folder_path = chunks_folder

        return True

    
    def add_user(self, user_id):
        pass

    def remove_user(self, user_id):
        pass
    
    def authorize(self, user_id):
        # Make sure the user is allowed to get this chunk
        ret = False
        # TODO TODO FINISH
        ret = True

        return ret
        
    def validate(self):
        # Make sure the chunk is good - e.g. valid and not corrupt
        ret = False

        # TODO TODO - FINISH
        ret = True
        return ret



def validate_user(user_id, auth_key):
    ret = False
    # See if the user is valid and if the auth_key is valid
    # TODO TODO - FINISH
    ret = True

    return ret

