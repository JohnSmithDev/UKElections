#!/usr/bin/env python3


import json
import pdb
import os
import re
import sys

from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify

try:
    from colorama import Fore, Back, Style
    COLOUR_AVAILABLE = True
except ImportError:
    COLOUR_AVAILABLE = False
    class Dummy(object):
        def __getattribute__(self, name):
            return ''
    Fore = Back = Style = Dummy()

COLORAMA_RESET = Fore.RESET + Back.RESET + Style.RESET_ALL

PARTY_COLOURS = {
    'conservative': Fore.WHITE + Back.BLUE,
    'labour': Fore.WHITE + Back.RED, # Note that this appears orange in some terminals?!?
    'liberal-democrats': Fore.BLACK + Back.YELLOW, # Should appear orange
    'green-party': Fore.WHITE + Back.LIGHTGREEN_EX,
    'speaker': Fore.WHITE + Back.LIGHTBLACK_EX,

    'snp': Fore.BLACK + Back.LIGHTYELLOW_EX,
    'plaid-cymru': Fore.BLACK + Back.GREEN, # Plaid should be darker than Green Party
    'dup': Fore.YELLOW + Back.LIGHTBLACK_EX,
    'sinn-fein': Fore.GREEN + Back.LIGHTBLACK_EX, # SF is even darker green than Green Party
    'independent': Fore.LIGHTWHITE_EX + Back.LIGHTBLACK_EX,
}



DEFAULT_PETITION_FILE= os.path.join(os.path.dirname(__file__), 'source_data',
                                    '241584_AsAt201903211007.json')
# EUREF_VOTES_BY_CONSTITUENCY_URL = 'https://commonslibrary.parliament.uk/' + \
#                                  'parliament-and-elections/elections-elections/' + \
#                                  'brexit-votes-by-constituency/'
EUREF_VOTES_BY_CONSTITUENCY_URL = 'http://tinyurl.com/ybnmmzz9'
def load_petition_data(petition_file):
    with open(petition_file) as petition_stream:
        petition_data = json.load(petition_stream)
    constituency_data = petition_data['data']['attributes']['signatures_by_constituency']
    # Turn this into a dict?
    ons2signatures = {}
    for constat in constituency_data:
        ons2signatures[ constat['ons_code'] ] = constat['signature_count']
    main_attributes = petition_data['data']['attributes']
    return (main_attributes['signature_count'], main_attributes['updated_at'],
            ons2signatures)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        petition_file = sys.argv[1]
    else:
        petition_file = DEFAULT_PETITION_FILE

    with open(os.path.join('intermediate_data', 'regions.json')) as regionstream:
        regions = json.load(regionstream)
    euref_data = load_and_process_euref_data()

    election_data = load_and_process_data(ADMIN_CSV, RESULTS_CSV, regions,
                                          euref_data)

    signature_count, petition_timestamp, petition_data = load_petition_data(petition_file)
    more_sigs = 0
    print('Based on petition data at %s (%d signatures)' % (petition_timestamp,
                                                            signature_count))
    print('Asterisked vote leave percentages are estimates - see %s' %
          EUREF_VOTES_BY_CONSTITUENCY_URL)

    for i, conres in enumerate(election_data, 1):
        margin = conres.winning_margin
        ons_code = conres.constituency.ons_code
        sigs = petition_data[ons_code]
        leave_pc = '%s%2d%%%s%s'  % (
            Back.MAGENTA if euref_data[ons_code].leave_pc >= 50.0 else '',
            euref_data[ons_code].leave_pc,
            ' ' if euref_data[ons_code].known_result else '*',
            COLORAMA_RESET)
        slug_party = slugify(conres.winning_party)
        # print(slug_party)
        margin_text = '%sGE2017 Winning margin: %5d votes%s   ' % \
                      (PARTY_COLOURS[slug_party], margin, COLORAMA_RESET)
        if sigs > margin:
            more_sigs += 1
            print('%3d. %-45s : Voted leave: %s    %s    Current signatures: %5d' %
                  (more_sigs, conres.constituency.name, leave_pc, margin_text, sigs))





