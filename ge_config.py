#!/usr/bin/env python3
"""
Configuration settings for the various General Elections we support.
"""

import os

SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'source_data')

GENERAL_ELECTIONS = {
    2015: {
        'constituencies_csv': os.path.join(SOURCE_DIR, '_2015_ge_', 'CONSTITUENCY.csv'),
        'results_csv': os.path.join(SOURCE_DIR, '_2015_ge_', 'RESULTS.csv'),
        'ruling_parties': ('Conservative', 'Speaker')
    },
    2017: {
        'constituencies_csv': os.path.join(SOURCE_DIR, '2017 UKPGE electoral data 3.csv'),
        'results_csv': os.path.join(SOURCE_DIR, '2017 UKPGE electoral data 4.csv'),
        'ruling_parties': ('Conservative', 'DUP', 'Speaker')
    },
    2019: {
        # There's no separate constituency file, but electorate is included in
        # the results.  With a bit of code tweaking I was able to get the
        # constituency data parsed with my existing code, but will need to
        # write some new stuff to parse the results
        # 'constituencies_csv': os.path.join(SOURCE_DIR, '2017 UKPGE electoral data 3.csv'),
        'constituencies_csv': os.path.join(SOURCE_DIR, '_2019_ge_', 'GE-2019-results.csv'),
        'combined_csv': os.path.join(SOURCE_DIR, '_2019_ge_', 'GE-2019-results.csv'),
        'ruling_parties': ('Conservative',),
        'data_credit': '@eldenvo',
        'data_url': 'https://twitter.com/eldenvo/status/1205525303092756482'
    }

}
