###### SequentialGUID
import os
import datetime
import sys
from binascii import unhexlify, hexlify
import uuid

class SequentialGUID:
    SEQUENTIAL_GUID_AS_STRING = 0
    SEQUENTIAL_GUID_AS_BINARY = 1
    SEQUENTIAL_GUID_AT_END = 2

    def __init__(self):
        pass

    @staticmethod
    def NewGUID(guid_type = SEQUENTIAL_GUID_AS_STRING):
        # What type of machine are we runing on?
        endian = sys.byteorder # will be 'little' or 'big'
        # Need some random info
        rand_bytes = bytearray()
        rand_bytes += os.urandom(10) #Get 10 random bytes

        # Get the current timestamp in miliseconds - makes this sequential
        ts = long((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
        tsbytes = bytearray()
        # NOTE: we don't pass endian into long_to_bytes
        tsbytes += long_to_bytes(ts) # Convert long to byte array
        while (len(tsbytes) < 8):  # Make sure to padd some 0s on the front so it is 64 bits
            tsbytes.insert(0, 0) # Python will most likely make it a byte array

        guid_bytes = bytearray(16) # 16 bytes is 128 bit


        # Combine the random and timestamp bytes into a GUID
        if(guid_type != SequentialGUID.SEQUENTIAL_GUID_AT_END):
            guid_bytes[0] = tsbytes[2]  # Copy timestamp into guid
            guid_bytes[1] = tsbytes[3]
            guid_bytes[2] = tsbytes[4]
            guid_bytes[3] = tsbytes[5]
            guid_bytes[4] = tsbytes[6]
            guid_bytes[5] = tsbytes[7]

            guid_bytes[6] = rand_bytes[0]  # Copy rand bytes into guid
            guid_bytes[7] = rand_bytes[1]
            guid_bytes[8] = rand_bytes[2]
            guid_bytes[9] = rand_bytes[3]
            guid_bytes[10] = rand_bytes[4]
            guid_bytes[11] = rand_bytes[5]
            guid_bytes[12] = rand_bytes[6]
            guid_bytes[13] = rand_bytes[7]
            guid_bytes[14] = rand_bytes[8]
            guid_bytes[15] = rand_bytes[9]
            if (guid_type == SequentialGUID.SEQUENTIAL_GUID_AS_STRING and endian == "little" and 1!=1):
                ## TODO: This is mucking things up for some reason hence the 1!=1
                # Need to swap stuff around if this is going to be string on little endian machines
                b = guid_bytes[0:4]  # First data chunk (4 items)
                b.reverse()
                guid_bytes[0] = b[0]
                guid_bytes[1] = b[1]
                guid_bytes[2] = b[2]
                guid_bytes[3] = b[3]

                b = guid_bytes[4:6] # 2nd data chunk (2 items)
                b.reverse()
                guid_bytes[4] = b[0]
                guid_bytes[5] = b[1]
                pass
            pass
        else:
            # Same as above, but different order - timestamp at end not beginning
            guid_bytes[10] = tsbytes[2]  # Copy timestamp into guid
            guid_bytes[11] = tsbytes[3]
            guid_bytes[12] = tsbytes[4]
            guid_bytes[13] = tsbytes[5]
            guid_bytes[14] = tsbytes[6]
            guid_bytes[15] = tsbytes[7]

            guid_bytes[0] = rand_bytes[0]  # Copy rand bytes into guid
            guid_bytes[1] = rand_bytes[1]
            guid_bytes[2] = rand_bytes[2]
            guid_bytes[3] = rand_bytes[3]
            guid_bytes[4] = rand_bytes[4]
            guid_bytes[5] = rand_bytes[5]
            guid_bytes[6] = rand_bytes[6]
            guid_bytes[7] = rand_bytes[7]
            guid_bytes[8] = rand_bytes[8]
            guid_bytes[9] = rand_bytes[9]
            pass

        # Create the guid and return it
        guid = uuid.UUID(hex=hexlify(guid_bytes))
        return guid


def long_to_bytes (val, endianness='big'):
    """ Pulled from http://stackoverflow.com/questions/8730927/convert-python-long-int-to-fixed-size-byte-array
    Use :ref:`string formatting` and :func:`~binascii.unhexlify` to
    convert ``val``, a :func:`long`, to a byte :func:`str`.

    :param long val: The value to pack

    :param str endianness: The endianness of the result. ``'big'`` for
      big-endian, ``'little'`` for little-endian.

    If you want byte- and word-ordering to differ, you're on your own.

    Using :ref:`string formatting` lets us use Python's C innards.
    """

    # one (1) hex digit per four (4) bits
    width = val.bit_length()

    # unhexlify wants an even multiple of eight (8) bits, but we don't
    # want more digits than we need (hence the ternary-ish 'or')
    width += 8 - ((width % 8) or 8)

    # format width specifier: four (4) bits per hex digit
    fmt = '%%0%dx' % (width // 4)

    # prepend zero (0) to the width, to zero-pad the output
    s = unhexlify(fmt % val)

    if endianness == 'little':
        # see http://stackoverflow.com/a/931095/309233
        s = s[::-1]

    return s

### Usage
### guid = SequentialGUID.NewSequentialGUID(SequentialGUID.SEQUENTIAL_GUID_AS_STRING)
### Use String for most dbs, and At End for MSSQL if you use their GUID field type
### REQUIRES: Python 2.6+ with bytearray support

###### End SequentailGUID
