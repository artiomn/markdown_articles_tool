"""Routines for the strings."""

import re
import unicodedata
from pathlib import Path
from typing import BinaryIO, Union, TextIO, List, Dict


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(r'[^\w\s-]', '', value.decode()).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)

    return value


def is_binary_same(s1: BinaryIO, s2: BinaryIO, bs: int = 4096) -> bool:
    """Return True if two binary streams are the same."""

    chunk = other = b'-'
    while chunk or other:
        chunk = s1.read(bs)
        other = s2.read(bs)
        if chunk != other:
            return False
    return True


def compare_files(filename1: Union[Path, str], filename2: Union[Path, str]) -> bool:
    """Compare files byte to byte."""

    with open(filename1, 'rb') as f1:
        with open(filename2, 'rb') as f2:
            return is_binary_same(f1, f2)


def replace_strings(replacement_mapping: Dict[str, str], text_stream: TextIO) -> List[str]:
    """Replace strings in the stream, using mapping."""

    lines = []
    for line in text_stream:
        for src, target in replacement_mapping.items():
            line = line.replace(src, str(target))
        lines.append(line)

    return lines
