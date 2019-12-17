#!/usr/bin/env python3
"""
Report on any issues detected between 2 sets of GE data - currently this is
just at the constituency level.  (Not sure what I might be able to useful
compare on results)

This is mainly to pick up any issues that might affect the visualizations and/or
issues with the source data.
"""

import logging
import pdb
import sys

from ge_config import GENERAL_ELECTIONS


from ec_data_reader import (load_and_process_data, ADMIN_CSV, RESULTS_CSV,
                            load_region_data)
from constituency import load_constituencies_from_admin_csv
from regions import constituency_name_to_region

def compare_constituency_data(c1, c2, label=None):
    """
    Compare data for the same constituency in 2 different general elections.
    It is assumed that c1 will be prior to c2 - this only makes any difference
    in terms of correctly logging if a change is positive vs negative.
    """
    # These should all be the same unless boundaries have changed.
    # It's possible names might have minor inconsistencies, but hopefully all
    # the important code uses ons_code or (less likely) pa_number
    for field in ('ons_code', 'pa_number', 'name'):
        f1 = getattr(c1, field)
        f2 = getattr(c1, field)
        if f1 != f2:
            logging.warning('%s: %s "%s" (%d) !- "%s" (%d)' % (label, field,
                                                               f1, c1.year,
                                                               f2, c2.year))
    electorate_diff = c2.electorate - c1.electorate
    electorate_pc_change = 100 * electorate_diff / c1.electorate
    print('%-50s: Electorate changed by %5d (%5.1f%%) : %-5d to %-5d' %
          (c1.name, electorate_diff,
           electorate_pc_change,
           c1.electorate, c2.electorate))

def compare_constituencies(years, regions):
    ge_data = {}
    num_constituencies = None
    for year in years:
        data = sorted(load_constituencies_from_admin_csv(
            GENERAL_ELECTIONS[year]['constituencies_csv'],
            regions), key=lambda z: z.ons_code)
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
        c1 = ge_data[years[0]][i]
        c2 = ge_data[years[1]][i]

        # Might be a good idea to set the year when the object is created?
        c1.year = years[0]
        c2.year = years[1]
        compare_constituency_data(c1, c2, label=f'Constituency#{i}')



def compare_everything(years, regions):
    ge_data = {}
    num_constituencies = None
    for year in years:
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
        cr1 = ge_data[years[0]][i]
        cr2 = ge_data[years[1]][i]


        # Might be a good idea to set the year when the object is created?
        cr1.year = years[0]
        cr2.year = years[1]

        compare_constituency_data(cr1.constituency, cr2.constituency,
                                  label=f'Constituency#{i}')



if __name__ == '__main__':
    if len(sys.argv) > 2:
        years = [int(z) for z in sys.argv[1:]]
    else:
        years = [2015, 2017] # Default to the only years we currently support

    regions_to_con_lists = load_region_data(add_on_countries=True)
    con_to_region = constituency_name_to_region(regions_to_con_lists)

    # This is currently broken for the 2019 data (due to different format)
    # compare_everything(years, regions_to_con_lists)


    compare_constituencies(years, con_to_region)
