#!/usr/bin/env python3
"""
Generic helper functions
"""

from decimal import Decimal
import re

# utf-8 blows up on the 0x96 (m-dash?) in the Electoral Commission CSVs
CSV_ENCODING = 'iso-8859-15'


def slugify(str):
    # The .replace() is for 'sinn-fein'
    # Python2 doesn't like the accent  in the above line - hacky workaround for now
    lc = str.lower()
    intermediate = re.sub('sinn f.in', 'sinn fein', lc)
    return re.sub('\W+', '-', intermediate)


def intify(s):
    """
    Convert a string (which may have commas in) to an int
    """
    return int(s.replace(',', ''))

def percentify(s):
    """
    Convert a string (which may have a trailing %) to a Decimal
    """
    return Decimal(s.replace('%', ''))


def output_file(output, filename):
    output.flush()
    with open(filename, mode='rb') as copystream:
        data = copystream.read()
        output.buffer.write(data)
