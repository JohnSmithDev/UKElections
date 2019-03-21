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
    return re.sub('\W+', '-', str.lower().replace(u'é', 'e'))


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

