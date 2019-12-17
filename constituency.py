#!/usr/bin/env python3
"""
Originally extracted from ec_data_reader.py
"""

import csv
import logging
import pdb
import re
import sys

from misc import intify, slugify, CSV_ENCODING

# ONS Code prefixes - https://en.wikipedia.org/wiki/ONS_coding_system#Current_GSS_coding_system
COUNTRY_CODE_PREFIXES = {
    'E14': 'England',
    'W07': 'Wales',
    'S14': 'Scotland',
    'N06': 'Northern Ireland'
    }

PYTHON_MAJOR_VERSION = sys.version_info[0]

if PYTHON_MAJOR_VERSION == 2:
    # appengine/py2 doesn't like encoding argument
    csv_reader_kwargs = {}
else:
    csv_reader_kwargs = {'encoding': CSV_ENCODING}



def clean_constituency_name(s):
    """
    # Clean up the following (why are they like this???):
    # ['Brecon and Radnorshire 5', 'Cardiff North 5',
    # 'Cardiff South and Penarth 5', 'Merthyr Tydfil and Rhymney 5',
    # 'Ogmore 5', 'Pontypridd 5', 'Vale of Glamorgan 5']
    # Plus Swansea East6...
    """
    name = re.sub('\s*\d+$', '', s.strip())

    # GE-2019-results.csv uses ampersands, turn these into "and" to (a) match
    # the Electoral Commission data, and (b) make life easier for HTML/SVG/XML
    name = name.replace('&', 'and')

    return name

class MissingColumnError(Exception):
    pass

def get_value_from_multiple_possible_keys(dict_from_csv_row, possible_keys,
                                          label='value'):
    for cn in possible_keys:
        try:
            return dict_from_csv_row[cn].strip()
        except KeyError:
            pass # Try the next one
    else:
        raise MissingColumnError('Could not find %s, tried %s' %
                                 (label, possible_keys))


class Constituency(object):
    """
    Given a CSVReader row for an "ADMINISTRATIVE DATA" or CONSTITUENCY.CSV row,
    return an object representing that constituency.

    Note that the CSV format is not consistent between elections :-(
    """

    def __init__(self, dict_from_csv_row, euref_data=None):
        self.ons_code = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['ONS Code', 'Constituency ID', 'code'],
            'ONS Code')
        # We don't *currently* use pa_number, so don't blow up if it's not there
        try:
            self.pa_number = int(get_value_from_multiple_possible_keys(
                dict_from_csv_row,
                # Note space at end of second element, also lower case "Association"
                ['Press association number', 'Press association number ', 'PANO'],
                'PA Number'))
        except MissingColumnError:
            self.pa_number = None

        name = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Constituency', 'Constituency Name', 'constituency'],
            'Constituency Name')
        self.name = clean_constituency_name(name)

        self.electorate = intify(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Electorate', 'Electorate ', 'electorate'], # Extraneous space is in 2017 data
            'Electorate'))
        self.valid_votes = intify(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            # Q: Does "turnout" (in 2019 file) include invalid votes?
            ['Total number of valid votes counted', 'Valid Votes', 'turnout'],
            'Valid Votes'))

        # 2015 CSV has a Region column, 2017 does not.
        # However we have to watch out for minor inconsistencies e.g.
        # "Yorkshire and [Th]he Humber"
        self._region = dict_from_csv_row.get('Region', None)

        # self.euref = euref_data[self.ons_code]
        self.euref = euref_data or None


    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, val):
        self._region = val

    @property
    def country(self):
        prefix = self.ons_code[:3]
        return COUNTRY_CODE_PREFIXES[prefix]

    @property
    def country_and_region(self):
        if self.region:
            return '%s - %s' % (self.country, self.region)
        else:
            return self.country

    def __repr__(self):
        return '%s (Electorate=%d)' % (self.name, self.electorate)



def sniff_admin_csv_for_ignorable_lines(admin_csv):
    """
    Given an admin CSV, read through the first few lines to work out how
    many are ignorable for the csv.DictReader, and return that number of lines
    (which may well be zero)
    """

    for skippable_lines, line in enumerate(open(admin_csv, 'r', **csv_reader_kwargs)):
        line_bits = set([z.strip().lower() for z in line.split(',')])
        if 'constituency' in line_bits or 'constituency name' in line_bits:
            # Q: is the file properly closed?  It doesn't seem to matter...
            return skippable_lines
        # print(line_bits)
    raise IOError('Could not determine skippable lines in %s' % (admin_csv))

def is_blank_row(row_dict):
    """
    Some of the CSVs have blank or semi-blank rows (e.g. a summary count of
    all votes in the 2015 RESULTS.csv file).  This will return True if the
    supplied CSVDictReader row dictionary is one such.

    NB: This (ab)uses the fact that both constituency and results CSVs have
    "Constituency"/"Constituency Name" columns, which might not be the case
    for future files.
    """

    try:
        name = get_value_from_multiple_possible_keys(
            row_dict,
            ['Constituency', 'Constituency Name', 'constituency'],
            'Constituency Name')
        if name and name != '':
            return False
        else:
            return True
    except MissingColumnError:
        return True

    ORIG_CODE = """
    try:
        con_name = row_dict['Constituency']
    except KeyError:
        con_name = row_dict['Constituency Name']
    if con_name and con_name != '':
        return False
    else:
        return True
    """

def get_region_for_constituency(con, con_to_region_map, quiet=False):
    """
    Given a Constituency object, use any of the various unique IDs to get a
    region from the provided dictionary.
    """
    if con.country and con.country != 'England':
        return con.country
    poss_keys = [str(getattr(con, prop)) for prop in ('name', 'ons_code', 'pa_number')]
    for val in poss_keys:
        try:
            return con_to_region_map[val]
        except KeyError:
            pass
    if not quiet:
        logging.warning('No region found for %s, trying slugified name...' % (poss_keys))
    slug = slugify(con.name)
    return con_to_region_map[slug]

def load_constituencies_from_admin_csv(admin_csv, con_to_region_map, quiet=False):
    """
    Return a list of Constituency objects
    """
    # ons_to_con_map = {}

    regions = set(con_to_region_map.values())
    slug_to_canonical_region_map = dict((slugify(r), r) for r in regions)

    ret = []
    skippable_lines = sniff_admin_csv_for_ignorable_lines(admin_csv)

    with open(admin_csv, 'r', **csv_reader_kwargs) as inputstream:
        # Ignore the first two rows, the useful headings are on the third row
        for _ in range(skippable_lines):
            xxx = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            # pdb.set_trace()
            # Note extraneous trailing space on 'Electorate ' :-(
            # print("%d %s %s" % (i, row['Constituency'], row['Electorate ']))
            if not is_blank_row(row):
                con = Constituency(row)
                if not con.region:
                    con.region = get_region_for_constituency(con, con_to_region_map, quiet)
                    ORIG = """
                    if con.country == 'England':
                        slug_con = slugify(con.name)
                        try:
                            con.region = con_to_region_map[slug_con]
                        except KeyError as err:
                            logging.error('No region found for %s/%s' % (con.name, slug_con))
                    """
                else:
                    con.region = slug_to_canonical_region_map[slugify(con.region)]
                ret.append(con)
    # return ons_to_con_map
    return ret
