#!/usr/bin/env python3
"""
Code for reading in region data, originally in ec_data_reader.py

Probably this should be merged in with extract_regions.py

"""

import json
import os

from ge_config import SOURCE_DIR, GENERAL_ELECTIONS
from misc import slugify
from constituency import load_constituencies_from_admin_csv

INTERMEDIATE_DIR = os.path.join(os.path.dirname(__file__), 'intermediate_data')

DEFAULT_REGION_FILE = os.path.join(INTERMEDIATE_DIR, 'regions.json')


# ONS Code prefixes - https://en.wikipedia.org/wiki/ONS_coding_system#Current_GSS_coding_system
COUNTRY_CODE_PREFIXES = {
    'E14': 'England',
    'W07': 'Wales',
    'S14': 'Scotland',
    'N06': 'Northern Ireland'
    }


def load_region_data(fn=DEFAULT_REGION_FILE, add_on_countries=False):
    """
    Return a dictionary mapping region to a list of constituency names
    """
    with open(fn) as regionstream:
        regions = json.load(regionstream)

    # Eh??? How did/does stuff uusing this return value ever work???
    # The above values are lists of consituencies.
    # The below values are strings of regions/countries
    # Update: I can see why the other code works now, but I'm still unconvinced
    # by this next bit...
    if add_on_countries:
        regions['Scotland'] = 'Scotland'
        regions['Wales'] = 'Wales'
        regions['Northern Ireland'] = 'Northern Ireland'

    return regions


def constituency_name_to_region(region_data, slugify_constituency_name=True,
                                key_mappings=None):
    """
    Reverse mapping of the output from load_region_data() i.e. constituency name->region
    By default the constituency name key is slugified.
    Alternatively, if key_mappings is a dict of str->list, the returned dict
    will have all constituency variant IDs mapped to the region e.g.
    * Constituency name
    * Slugified constituency name
    * ONS Code
    * PA number
    But all this is entirely dependent on what is in key_mappings - which can
    be set up with constituency_id_mappings

    """
    con_to_region = {} # reverse map constituency name
    for reg, con_list in region_data.items():
        for con in con_list:
            if key_mappings:
                for k in key_mappings[con]:
                    con_to_region[k] = reg
            else:
                k = (slugify(con) if slugify_constituency_name else con)
                con_to_region[k] = reg
    return con_to_region

DEFAULT_CONSTITUENCY_CSV = GENERAL_ELECTIONS[2017]['constituencies_csv']


def constituency_id_mappings(constituency_csv=DEFAULT_CONSTITUENCY_CSV):
    basic_regions = load_region_data(add_on_countries=True)
    con_to_region = constituency_name_to_region(basic_regions)

    ge2017_data = load_constituencies_from_admin_csv(constituency_csv,
                                                     con_to_region)
    c2ids_map = {}
    for con in ge2017_data:
        ids = [con.name, slugify(con.name),
                               con.ons_code]
        if con.pa_number:
             # Keep consistent with other values' type to allow for sorting
            ids.append(str(con.pa_number))
        c2ids_map[con.name] = ids
    return c2ids_map
