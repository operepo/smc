import re
import uuid
import threading
import os
import base64

# Deal with change to web2py - moved AES to pyaes folder
#import gluon.contrib.aes as AES
import gluon.contrib.pyaes as AES
#import ednet.aes as AES

def natural_key(string_):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

###### Encrypt Filters for Encrypted Fields
## To use:
## 1 - Set a variable called x_app_enc_key (16, 24, or 32 bytes)
# Moved to Util class as aes_key
#x_app_enc_key = 'ALFKJOIUXETRKH@&YF(*&Y#$9a78sd:O'
## 2 - add the following filters for each field to encrypt
    ## db.t_test.f_field.filter_in = lambda value : w2p_encrypt(value)
    ## db.t_test.f_field.filter_out = lambda value : w2p_decrypt(value)


def fast_urandom16(urandom=[], locker=threading.RLock()):
    """
    this is 4x faster than calling os.urandom(16) and prevents
    the "too many files open" issue with concurrent access to os.urandom()
    """
    try:
        return urandom.pop()
    except IndexError:
        try:
            locker.acquire()
            ur = os.urandom(16 * 1024)
            urandom += [ur[i:i + 16] for i in xrange(16, 1024 * 16, 16)]
            return ur[0:16]
        finally:
            locker.release()

def pad(s, n=32, padchar=' '):
    if len(s) == 0:
        # Handle empty value - pad it out w empty data
        s += padchar * n
        return s
    while ((len(s) % n) != 0):
        s += padchar
    #pad_len = len(s) % 32 # How many characters do we need to pad out to a multiple of 32
    #if (pad_len != 0):
    #    #return s + (32 - len(s) % 32) * padchar
    #    return s + (
    return s


###### END Encrypt Filters for Encrypted Fields



class Util:
    aes_key = 'ALFKJOIUXETRKH@&YF(*&Y#$9a78sd:O'
    
    def __init__(self):
        pass
    
    @staticmethod
    def AES_new(key, iv=None):
        Util.aes_key = key
        """ Returns an AES cipher object and random IV if None specified """
        if iv is None:
            iv = fast_urandom16()

        #return AES.new(key, AES.MODE_CBC, IV), IV
        #Util.aes = pyaes.AESModeOfOperationCBC(key, iv = iv)
        #plaintext = "TextMustBe16Byte"
        #ciphertext = aes.encrypt(plaintext)
        return AES.AESModeOfOperationCBC(key, iv = iv), iv
    
    @staticmethod
    def encrypt(data, lkey=None):
        if not lkey is None:
            key = lkey
        else:
            key = Util.aes_key
        key = pad(key[:32])
        cipher, iv = Util.AES_new(key)
        encrypted_data = iv + cipher.encrypt(pad(data, 16))
        return base64.urlsafe_b64encode(encrypted_data)

    @staticmethod
    def decrypt(data, lkey=None):
        if not lkey is None:
            key = lkey
        else:
            key = Util.aes_key
        key = pad(key[:32])
        if (data == None):
            data = ""
        try:
            data = base64.urlsafe_b64decode(data)
        except TypeError as ex:
            # Don't let error blow things up
            pass
        iv, data = data[:16], data[16:]
        try:
            cipher, _ = Util.AES_new(key, iv=iv)
        except:
            # bad IV = bad data
            return data
        try:
            data = cipher.decrypt(data)
        except:
            # Don't let error blow things up
            pass
        data = data.rstrip(' ')
        return data

    @staticmethod
    def GetModList(attr_list, mod_op=None):
        modlist = []
        for attrtype in attr_list.keys():
            attrvaluelist = filter(lambda x:x!=None, attr_list[attrtype])
            if attrvaluelist:
                if (mod_op != None):
                    modlist.append((mod_op, attrtype, attr_list[attrtype]))
                else:
                    modlist.append((attrtype, attr_list[attrtype]))
        return modlist

    @staticmethod
    def GetCellValue(sheet, row, col, default_val=""):
        ret = default_val
        try:
            val = str(sheet.cell(row, col).value)
            # Strips off the .0 at the end of numbers
            if (val.endswith(".0")):
                val = val[:-2]
            ret = val
        except:
            #ret = "ERROR!!!"
            pass
        return ret

    @staticmethod
    def GetJSONFromCellRange(sheet, row, col_start, col_end):
        from gluon.serializers import json
        # Loop through the cols and add them do an array
        items = dict()
        for col in range(col_start, col_end):
            items["col_"+str(col)] = Util.GetCellValue(sheet, row, col)

        json_cols = json(items)
        return json_cols

    @staticmethod
    def ParseName(full_name):
        # Split name into parts
        pos = full_name.find(",")
        if (pos != -1):
            # Found comma, should be last name first
            parts = full_name.split(',', 2)
            parts = (parts[1].strip(), parts[0].strip())
            return parts

        # Assume first <space> last format
        parts = full_name.split(None, 2)
        if (len(parts) > 1):
            parts = (parts[0].strip(), parts[1].strip())
        elif (len(parts) == 1):
            parts = (parts[0].strip())
        return parts
