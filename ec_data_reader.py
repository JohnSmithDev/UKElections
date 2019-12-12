#!/usr/bin/env python3
"""
Turn the Electoral Commission CSVs into Python objects that can be manipulated.

This is for the 2017 CSV data, the 2015 version is a slightly different format.
TODO: support 2015, ideally having as much common code as possible
"""

from collections import defaultdict
import csv
from decimal import Decimal
import json
import logging
import os
import pdb
import re
import sys

PYTHON_MAJOR_VERSION = sys.version_info[0]

from misc import slugify, intify, percentify, CSV_ENCODING
from canonical_party_names import CANONICAL_PARTY_NAMES

if PYTHON_MAJOR_VERSION == 2:
    # appengine/py2 doesn't like encoding argument
    csv_reader_kwargs = {}
else:
    csv_reader_kwargs = {'encoding': CSV_ENCODING}


SOURCE_DIR = 'source_data'


# TODO: deprecate these next two in favour of DATA_SETS
ADMIN_CSV = os.path.join('source_data', '2017 UKPGE electoral data 3.csv')
RESULTS_CSV = os.path.join('source_data', '2017 UKPGE electoral data 4.csv')


# ONS Code prefixes - https://en.wikipedia.org/wiki/ONS_coding_system#Current_GSS_coding_system
COUNTRY_CODE_PREFIXES = {
    'E14': 'England',
    'W07': 'Wales',
    'S14': 'Scotland',
    'N06': 'Northern Ireland'
    }



def clean_constituency_name(s):
    """
    # Clean up the following (why are they like this???):
    # ['Brecon and Radnorshire 5', 'Cardiff North 5',
    # 'Cardiff South and Penarth 5', 'Merthyr Tydfil and Rhymney 5',
    # 'Ogmore 5', 'Pontypridd 5', 'Vale of Glamorgan 5']
    # Plus Swansea East6...
    """
    name = re.sub('\s*\d+$', '', s.strip())
    return name


class ConstituencyCreationError(Exception):
    pass

def get_value_from_multiple_possible_keys(dict_from_csv_row, possible_keys,
                                          label='value'):
    for cn in possible_keys:
        try:
            return dict_from_csv_row[cn].strip()
        except KeyError:
            pass # Try the next one
    else:
        raise ConstituencyCreationError('Could not find %s, tried %s' %
                                        (label, column_names))


class Constituency(object):
    """
    Given a CSVReader row for an "ADMINISTRATIVE DATA" or CONSTITUENCY.CSV row,
    return an object representing that constituency.

    Note that the CSV format is not consistent between elections :-(
    """

    def __init__(self, dict_from_csv_row, euref_data=None):
        self.ons_code = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['ONS Code', 'Constituency ID'],
            'ONS Code')
        self.pa_number = int(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            # Note space at end of second element, also lower case "Association"
            ['Press association number', 'Press association number ', 'PANO'],
            'PA Number'))

        name = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Constituency', 'Constituency Name'],
            'Constituency Name')
        self.name = clean_constituency_name(name)

        self.electorate = intify(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Electorate', 'Electorate '], # Extraneous space is in 2017 data
            'Electorate'))
        self.valid_votes = intify(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Total number of valid votes counted', 'Valid Votes'],
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


# Do we need the party class, or can we just use strings based on the 'Party
# Identifer' (sic) column?  I'm assuming the latter for now
class XXX_Party(object):
    def __init__(self, dict_from_csv_row):
        try:
            # Another error I live in hope that they fix
            self.party_id = dict_from_csv_row['Party Identifier'].strip()
        except KeyError:
            self.party_id = dict_from_csv_row['Party Identifer'].strip()
        # Note that the Party column (F) is more of a "free-text" thing that
        # includes stuff like "The Conservative Party Candidate". "UK
        # Independence Party (UKIP)", "Labour and Cooperative", etc
        # Party Identifer (sic) seems to be a normalzed value, although still
        # a bit irregular for Independents

    def __repr__(self):
        return self.party_id


class CandidateResult(object):
    def __init__(self, dict_from_csv_row, ons_to_con_map):
        # ons_code = dict_from_csv_row['ONS Code'].strip() # 2017 only
        ons_code = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['ONS Code', 'Constituency ID', 'Constituency ID '],
            'ONS Code')
        self.constituency = ons_to_con_map[ons_code]
        OLD_CODE_FOR_2017_ONLY = """
        try:
            self.party = dict_from_csv_row['Party Identifier'].strip()
        except KeyError:
            self.party = dict_from_csv_row['Party Identifer'].strip()
        self.valid_votes = intify(dict_from_csv_row['Valid votes'])
        """
        raw_party = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Party Identifier', 'Party Identifer', 'Party name identifier'],
            'Party ID')
        self.party = CANONICAL_PARTY_NAMES.get(raw_party, raw_party)
        self.valid_votes = intify(get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Valid votes', 'Votes'],
            'Votes'))
        # TODO (maybe?): Candidate name

    def __repr__(self):
        return '%s got %d votes in %s' % (self.party, self.valid_votes,
                                          self.constituency)

class ConstituencyResult(object):
    def __init__(self, results):
        self.results = sorted(results, key=lambda z: z.valid_votes,
                              reverse=True)
        # Q: How is the winner indicated if there was a tie?  Does the
        # returning officer add 1 to the winner?
        self.winning_result = self.results[0]
        self.constituency = self.winning_result.constituency
        self.winning_party = self.winning_result.party

        if len(self.results) > 1:
            self.winning_margin = self.winning_result.valid_votes - \
                                  self.results[1].valid_votes
        else:
            # Highly unlikely to happen, but you never know...
            self.winning_margin = self.winning_result.valid_votes

        # Q: Technically turnout includes invalid votes?
        self.turnout_pc = Decimal(100 * self.constituency.valid_votes / self.constituency.electorate)

        # Q: should this be divided by valid_votes, not electorate?
        #    That seems to be what Wikipedia are using e.g. Tottenham 2017
        #    has 70.1% majority on Wikipedia, but only ~47% using electorate
        self.margin_pc = Decimal(100 * self.winning_margin / self.constituency.electorate)
        self.margin_pc = Decimal(100 * self.winning_margin / self.constituency.valid_votes)


    def __repr__(self):
        return '%s won %s by %d votes' % (self.winning_party, self.constituency,
                                          self.winning_margin)


def load_region_data(fn=None, add_on_countries=False):
    """
    Return a dictionary mapping region to a list of constituency names
    """
    if not fn:
        fn = os.path.join('intermediate_data', 'regions.json')
    with open(fn) as regionstream:
        regions = json.load(regionstream)
    if add_on_countries:
        regions['Scotland'] = 'Scotland'
        regions['Wales'] = 'Wales'
        regions['Northern Ireland'] = 'Northern Ireland'

    return regions

def constituency_name_to_region(region_data, slugify_constituency_name=True):
    """
    Reverse mapping of the output from load_region_data() i.e. constituency name->region
    By default the constituency name key is slugified
    """
    con_to_region = {} # reverse map constituency name
    for reg, con_list in region_data.items():
        for con in con_list:
            k = (slugify(con) if slugify_constituency_name else con)
            con_to_region[k] = reg
    return con_to_region


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
        con_name = row_dict['Constituency']
    except KeyError:
        con_name = row_dict['Constituency Name']
    if con_name and con_name != '':
        return False
    else:
        return True


def load_constituencies_from_admin_csv(admin_csv, con_to_region_map):
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
                    if con.country == 'England':
                        slug_con = slugify(con.name)
                        try:
                            con.region = con_to_region_map[slug_con]
                        except KeyError as err:
                            logging.error('No region found for %s/%s' % (con.name, slug_con))
                else:
                    con.region = slug_to_canonical_region_map[slugify(con.region)]
                ret.append(con)
    # return ons_to_con_map
    return ret

def sniff_results_csv_for_ignorable_lines(results_csv):
    """
    Given a results CSV, read through the first few lines to work out how
    many are ignorable for the csv.DictReader, and return that number of lines
    (which may well be zero).

    Note this is currently functionally identical to sniff_admin_csv_for_ignorable_lines()
    due to both files having Constituency/Constituency Name columns.
    """

    for skippable_lines, line in enumerate(open(results_csv, 'r', **csv_reader_kwargs)):
        line_bits = set([z.strip().lower() for z in line.split(',')])
        if 'constituency' in line_bits or 'constituency name' in line_bits:
            # Q: is the file properly closed?  It doesn't seem to matter...
            return skippable_lines
        # print(line_bits)
    raise IOError('Could not determine skippable lines in %s' % (results_csv))

def load_and_process_data(admin_csv, results_csv, regions, euref_data=None):
    """
    Return a list of ConstituencyResult objects
    """
    con_to_region = constituency_name_to_region(regions)

    constituency_list = load_constituencies_from_admin_csv(admin_csv, con_to_region)

    ons_to_con_map = {}
    for con in constituency_list:
        ons = con.ons_code
        ons_to_con_map[ons] = con
        if euref_data:
            con.euref = euref_data[con.ons_code]

    raw_results = defaultdict(list)
    skippable_lines = sniff_results_csv_for_ignorable_lines(results_csv)
    with open(results_csv, 'r', **csv_reader_kwargs) as inputstream:
        for _ in range(skippable_lines):
            xxx = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            if not is_blank_row(row):
                can_res = CandidateResult(row, ons_to_con_map)
                raw_results[can_res.constituency.ons_code].append(can_res)


    processed_results = []
    # Not sure whether this sort gives better results than the one below
    for _, raw_res in raw_results.items():
        processed_results.append(ConstituencyResult(raw_res))

    # Python 3 IIRC honours the insert order of a dict, so we didn't need to sort
    # Python 2 doesn't, hence the sorted() here to ensure some consistency
    # Note that this ordering differs from the one that was inherited from the
    # CSV (which I think was region, then constituency name)
    return sorted(processed_results, key=lambda z: z.constituency.name)
    # return processed_results


if __name__ == '__main__':
    admin_csv = ADMIN_CSV
    results_csv = RESULTS_CSV
    if len(sys.argv) > 1:
        admin_csv = sys.argv[1]
    if len(sys.argv) > 2:
        results_csv = sys.argv[2]

    region_data = load_region_data(add_on_countries=True)

    from euref_data_reader import load_and_process_euref_data
    euref_data = load_and_process_euref_data()

    results = load_and_process_data(admin_csv, results_csv, region_data, euref_data)
    print(results[0])
    print(results[0].constituency)
    print(results[0].constituency.euref)



