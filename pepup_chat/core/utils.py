import binascii
import os


def get_random_md5():
    return binascii.hexlify(os.urandom(128))


def get_random_hex_string(digit):
    return binascii.hexlify(os.urandom(digit >> 1))
