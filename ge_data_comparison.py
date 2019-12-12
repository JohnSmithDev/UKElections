#!/usr/bin/env python3
"""
Report on any issues detected between 2 sets of GE data.

This is mainly to pick up any issues that might affect the visualizations and/or
issues with the source data.
"""

import logging
import pdb
import sys

from ge_config import GENERAL_ELECTIONS


from ec_data_reader import (load_and_process_data, ADMIN_CSV, RESULTS_CSV,
                            load_region_data)


def compare_constituency_data(cr1, cr2, label=None):
    """
    Compare data for the same constituency in 2 different general elections.
    It is assumed that c1 will be prior to c2 - this only makes any difference
    in terms of correctly logging if a change is positive vs negative.
    """
    # These should all be the same unless boundaries have changed.
    # It's possible names might have minor inconsistencies, but hopefully all
    # the important code uses ons_code or (less likely) pa_number
    c1 = cr1.constituency
    c2 = cr2.constituency
    for field in ('ons_code', 'pa_number', 'name'):
        f1 = getattr(c1, field)
        f2 = getattr(c1, field)
        if f1 != f2:
            logging.warning('%s: %s "%s" (%d) !- "%s" (%d)' % (label, field,
                                                               f1, c1.year,
                                                               f2, c2.year))
    electorate_diff = c2.electorate - c1.electorate
    electorate_pc_change = 100 * electorate_diff / c1.electorate
    print('%-50s: Electorate changed by %5d (%5.1f%%)' % (c1.name, electorate_diff,
                                                        electorate_pc_change))


if __name__ == '__main__':
    if len(sys.argv) > 2:
        YEARS = [int(z) for z in sys.argv[1:]]
    else:
        YEARS = [2015, 2017] # Default to the only years we currently support

    regions = load_region_data(add_on_countries=True)

    ge_data = {}
    num_constituencies = None
    for year in YEARS:
        data = load_and_process_data(
            GENERAL_ELECTIONS[year]['constituencies_csv'],
            GENERAL_ELECTIONS[year]['results_csv'],
            regions)
        ge_data[year] = data
        if num_constituencies is None:
            num_constituencies = len(data)
        elif num_constituencies != len(data):
            logging.warning('Number of constituencies in %d is %d, expected %d' %
                            (year, len(data), num_constituencies))
        print('%d : %d constituencies' % (year, len(data)))

    # Assumption that the constituency data is sorted in a consistent manner e.g.
    # name, PA code, not electorate, winning marging, etc etc
    for i in range(num_constituencies):
        c1 = ge_data[YEARS[0]][i]
        c2 = ge_data[YEARS[1]][i]

        # Might be a good idea to set the year when the object is created?
        c1.year = YEARS[0]
        c2.year = YEARS[1]

        compare_constituency_data(c1, c2, label=f'Constituency#{i}')


