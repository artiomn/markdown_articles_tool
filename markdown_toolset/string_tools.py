"""
Routines for the strings.
"""

import re
import unicodedata
from typing import BinaryIO


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(r'[^\w\s-]', '', value.decode()).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)

    return value


def is_binary_same(s1: BinaryIO, s2: BinaryIO, bs: int = 4096):
    """
    Return True if two binary streams are the same.
    """

    chunk = other = True
    while chunk or other:
        chunk = s1.read(bs)
        other = s2.read(bs)
        if chunk != other:
            return False
    return True
