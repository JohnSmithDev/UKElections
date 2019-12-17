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
    Convert a string (which may have commas in) to an int.

    The intermediate float casting is to handle scientific notation like
    "9.00E+03" in the 2019 Brigg and Google data.
    """
    return int(float(s.replace(',', '')))

def percentify(s):
    """
    Convert a string (which may have a trailing %) to a Decimal
    """
    return Decimal(s.replace('%', ''))


def output_file(output, filename, value_map=None):
    output.flush()
    # Hmm - this was previously opened with "mode='rb'" - however that stops
    # us from using .format_map().  Was that a Python 2 hack?  If so, I'll
    # remove it, but keep this comment in case there's more to it...
    with open(filename) as copystream:
        data = copystream.read()
        if value_map:
            data = data.format_map(value_map)
        # This was output.buffer.write(data) when mode='rb' was enabled
        output.write(data)
