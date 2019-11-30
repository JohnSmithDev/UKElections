#!/usr/bin/env python3
"""
Turn the Electoral Commission CSVs into Python objects that can be manipulated.
"""

from collections import defaultdict
import csv
from decimal import Decimal
import logging
import os
import pdb
import re
import sys

PYTHON_MAJOR_VERSION = sys.version_info[0]

from misc import slugify, intify, percentify, CSV_ENCODING

if PYTHON_MAJOR_VERSION == 2:
    # appengine/py2 doesn't like encoding argument
    csv_reader_kwargs = {}
else:
    csv_reader_kwargs = {'encoding': CSV_ENCODING}

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


class Constituency(object):

    def __init__(self, dict_from_csv_row, euref_data=None):
        self.ons_code = dict_from_csv_row['ONS Code']
        try:
            self.pa_number = dict_from_csv_row['Press association number']
        except KeyError:
            # Another dodgy column name
            self.pa_number = dict_from_csv_row['Press association number ']
        self.name = clean_constituency_name(dict_from_csv_row['Constituency'])


        try:
            # I live in hope that one day the extraneous space will be removed
            self.electorate = intify(dict_from_csv_row['Electorate'])
        except KeyError:
            self.electorate = intify(dict_from_csv_row['Electorate '])
        self.valid_votes = intify(dict_from_csv_row['Total number of valid votes counted'])

        self._region = None
        if euref_data:
            self.euref = euref_data[self.ons_code]


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
class Party(object):
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
        ons_code = dict_from_csv_row['ONS Code'].strip()
        self.constituency = ons_to_con_map[ons_code]
        try:
            self.party = dict_from_csv_row['Party Identifier'].strip()
        except KeyError:
            self.party = dict_from_csv_row['Party Identifer'].strip()
        self.valid_votes = intify(dict_from_csv_row['Valid votes'])
        # TODO: Candidate name

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


def load_and_process_data(admin_csv, results_csv, regions, euref_data=None):
    """
    Return a list of ConstituencyResult objects
    """
    con_to_region = {}
    for reg, con_list in regions.items():
        for con in con_list:
            con_to_region[slugify(con)] = reg

    ons_to_con_map = {}
    with open(admin_csv, 'r', **csv_reader_kwargs) as inputstream:
        # Ignore the first two rows, the useful headings are on the third row
        xxx = inputstream.readline()
        yyy = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            # pdb.set_trace()
            # Note extraneous trailing space on 'Electorate ' :-(
            # print("%d %s %s" % (i, row['Constituency'], row['Electorate ']))
            con_name = row['Constituency']
            if con_name: # avoid blank rows
                con = Constituency(row, euref_data)
                ons_to_con_map[con.ons_code] = con
                if con.country == 'England':
                    slug_con = slugify(con.name)
                    try:
                        con.region = con_to_region[slug_con]
                    except KeyError as err:
                        logging.error('No region found for %s/%s' % (con.name, slug_con))


    raw_results = defaultdict(list)
    with open(results_csv, 'r', **csv_reader_kwargs) as inputstream:
        # Ignore the first row, the useful headings are on the second row
        _ = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            # pdb.set_trace()
            # Note extraneous trailing space on 'Electorate ' :-(
            # print("%d %s %s" % (i, row['Constituency'], row['Electorate ']))
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
    results = load_and_process_data(ADMIN_CSV, RESULTS_CSV)


    pdb.set_trace()



