#!/usr/bin/env python3
"""
Read in EUReferendumByConstituency.csv, which is an export of the "DATA"
sheet from eureferendum_constitunecy.xlsx (sic) downloadable from
https://commonslibrary.parliament.uk/parliament-and-elections/elections-elections/brexit-votes-by-constituency/
"""

import csv
from decimal import Decimal
import os
import pdb
import sys

from misc import intify, percentify, CSV_ENCODING # CSV_ENCODING perhaps not needed here?

EUREF_CSV = os.path.join('source_data', 'EUReferendumByConstituency.csv')


class EUReferendumResult(object):
    def __init__(self, row_dict):
        self.ons_code = row_dict['ONS ID']
        self.name = row_dict['Constituency']
        self.known_result = (row_dict['result'].strip() == 'Yes')
        self.leave_pc = percentify(row_dict['TO USE'])

    @property
    def voted_to_leave(self):
        return self.leave_pc > 50 # Q: Should this be >= ?

    def __repr__(self):
        return '%s voted %s for Leave' % (self.name, self.leave_pc)

def load_and_process_euref_data(csvfile=EUREF_CSV):
    """
    Return a dict mapping ONS codes to EUReferendumResult objects
    """
    results = {}
    with open(csvfile, 'r', encoding=CSV_ENCODING) as inputstream:
        # Ignore the first five rows, useful headings are on row 6
        # (Strictly speaking the headers are split over rows 4-6, sigh...)
        for _ in range(5):
            __ = inputstream.readline()
        reader = csv.DictReader(inputstream)
        for i, row in enumerate(reader):
            # First 2 rows after the headings are also bogus
            if not row['ONS ID']:
                continue
            else:
                eurr = EUReferendumResult(row)
                results[eurr.ons_code] = eurr
    return results

if __name__ == '__main__':
    results =  load_and_process_euref_data()
    # pdb.set_trace()
