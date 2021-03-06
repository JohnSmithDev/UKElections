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
from regions import (COUNTRY_CODE_PREFIXES, load_region_data,
                     constituency_name_to_region, constituency_id_mappings)
from constituency import (Constituency, get_value_from_multiple_possible_keys,
                          MissingColumnError, is_blank_row,
                          load_constituencies_from_admin_csv)

if PYTHON_MAJOR_VERSION == 2:
    # appengine/py2 doesn't like encoding argument
    csv_reader_kwargs = {}
else:
    csv_reader_kwargs = {'encoding': CSV_ENCODING}


SOURCE_DIR = 'source_data'


# TODO: deprecate these next two in favour of ge_config.GENERAL_ELECTIONS
ADMIN_CSV = os.path.join('source_data', '2017 UKPGE electoral data 3.csv')
RESULTS_CSV = os.path.join('source_data', '2017 UKPGE electoral data 4.csv')




        return COUNTRY_CODE_PREFIXES[prefix]

    @property
    def country_and_region(self):
        if self.region:
            return '%s - %s' % (self.country, self.region)
        else:
            return self.country

    def __repr__(self):
        return '%s (Electorate=%d)' % (self.name, self.electorate)




class CandidateResult(object):
    def __init__(self, dict_from_csv_row, ons_to_con_map):
        ons_code = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['ONS Code', 'Constituency ID', 'Constituency ID ', 'code'],
            'ONS Code')
        self.constituency = ons_to_con_map[ons_code]
        raw_party = get_value_from_multiple_possible_keys(
            dict_from_csv_row,
            ['Party Identifier', 'Party Identifer', 'Party name identifier', 'party'],
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

def load_and_process_data_2019(data_csv, regions, euref_data=None):
    """
    Return a list of ConstituencyResult objects.

    TODO: this is a dirty hack of the above function, properly refactor
    """
    regions = load_region_data() # NOTE WE GET RID OF THE COUNTRY HACKS!!!!!
    con_name_to_ids = constituency_id_mappings()
    con_to_region = constituency_name_to_region(regions, key_mappings=con_name_to_ids)

    constituency_list = load_constituencies_from_admin_csv(data_csv, con_to_region)

    ons_to_con_map = {}
    for con in constituency_list:
        ons = con.ons_code
        ons_to_con_map[ons] = con
        if euref_data:
            con.euref = euref_data[con.ons_code]

    raw_results = defaultdict(list)
    # skippable_lines = sniff_results_csv_for_ignorable_lines(results_csv)
    skippable_lines = 0
    with open(data_csv, 'r', **csv_reader_kwargs) as inputstream:
        for _ in range(skippable_lines):
            xxx = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            if not is_blank_row(row):
                unsorted_results = []
                for party in 'all,brx,con,dup,grn,ind,lab,lib,oth,plc,sdl,snf,snp,spk,ukp,uup'.split(','):
                    fake_row_dict = {
                        'code': row['code'],
                        'constituency': row['constituency'],
                        'party': party,
                        'Valid votes': row[party]
                        }
                    can_res = CandidateResult(fake_row_dict, ons_to_con_map)
                    unsorted_results.append(can_res)
                raw_results[can_res.constituency.ons_code] = sorted(
                    unsorted_results,
                    key=lambda z:-z.valid_votes)


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

    if admin_csv == results_csv:
        results = load_and_process_data_2019(admin_csv, region_data, euref_data)
    else:
        results = load_and_process_data(admin_csv, results_csv, region_data, euref_data)
    print(results[0])
    print(results[0].constituency)
    print(results[0].constituency.euref)



