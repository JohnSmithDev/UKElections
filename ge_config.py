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
    }

}
