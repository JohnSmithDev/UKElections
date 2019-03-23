#!/usr/bin/env python3

from __future__ import division # Has to be usable as a Python 2 library

import json
import pdb
import os
import re
import sys

from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify,  output_file
from grab_latest_petition_data import check_latest_petition_data

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
                                    '241584_AsAt201903211040.json')
EUREF_VOTES_BY_CONSTITUENCY_URL = 'https://commonslibrary.parliament.uk/' + \
                                  'parliament-and-elections/elections-elections/' + \
                                  'brexit-votes-by-constituency/'
EUREF_VOTES_BY_CONSTITUENCY_SHORT_URL = 'http://tinyurl.com/ybnmmzz9'
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

def py2print(txt):
    # Hacky wrapper for Python 2 - obviously this only works for the most
    # basic print() usage.  (Could be made better, but would rather port to Py3)
    print(txt)

def html_header(output_function, embed):
        title = '''Analysis of Revoke Article 50 petition vs General Election 2017
                     and EU Referendum results'''

        output_function('''<!DOCTYPE html>\n<html lang="en-GB">\n<head>''')
        output_function('<meta charset="utf-8" />\n') # Not sure if this is right, but FF whinges otherwise
        # output_file(sys.stdout, 'table_colours.css')
        # output_function('.voted-leave { background: purple; color: white; }</style>')
        if embed:
            output_function('<style>\n')
            output_file(sys.stdout, os.path.join('static', 'table_colours.css'))
            output_function('</style>\n')
        else:
            output_function('''<link rel="stylesheet" type="text/css"
                  href="/static/table_colours.css" />\n''')

        output_function('<title>%s</title></head>\n' % (title))

        output_function('<body>\n')
        if embed:
            output_function('<script>\n')
            output_file(sys.stdout, os.path.join('static', 'sorttable.js'))
            output_function('</script>\n')
        else:
            output_function('''<script src="/static/sorttable.js"></script>\n''')

        output_function('<h1>%s</h1>\n' % (title))

def sub_header(output_function, petition_timestamp, signature_count,
               constituency_total, sig_above_margin, pro_leave_sig_above_margin):
        output_function('''<p>Based on
<a href="https://petition.parliament.uk/petitions/241584" rel="nofollow">petition</a>
<a href="https://petition.parliament.uk/petitions/241584.json" rel="nofollow">data</a>
        at %s - <b>%d signatures</b> of which <b>%d (%d%%)</b> are associated with a
parliamentary constituency</p>''' % (petition_timestamp, signature_count,
                                      constituency_total,
                                      100 * constituency_total / signature_count))

        output_function('''<p>Asterisked vote leave percentages are estimates -
         see <a href="%s">this link</a>.  2017 General Election data
        from the <a href="https://www.electoralcommission.org.uk/our-work/our-research/electoral-data/electoral-data-files-and-reports">Electoral Commission</a>.''' %  EUREF_VOTES_BY_CONSTITUENCY_URL)

        output_function('Party colours via <a href="https://en.wikipedia.org/wiki/2017_United_Kingdom_general_election#Full_results">Wikipedia</a>.</p>')
        output_function('''<p><a href="https://github.com/JohnSmithDev/UKElections">Code</a>
               by <a href="https://twitter.com/JohnMMIX">John Smith</a>.
Table sorting (click on the headers) via <a href="https://www.kryogenix.org/code/browser/sorttable/">sorttable</a>.
</p>''')

        output_function('''<h2>%d constituencies currently have more petition signatures
        than their GE2017 winning margin, of which %d voted in favour of leaving in
        the 2016 EU Referendum</h2>''' %
              (sig_above_margin, pro_leave_sig_above_margin))


        output_function('<table class="sortable">\n<tr>\n')
        output_function('''<th></th><th>Constituency</th><th>Voted leave percentage</th>
        <th>GE 2017 winning margin (# votes)</th><th>Current petition signatures</th>
    <th>Percentage of electorate</th><th>Petition to winning margin ratio</th>''')

def process(petition_file, html_output=True, include_all=True, output_function=py2print,
            embed=True):

    with open(os.path.join('intermediate_data', 'regions.json')) as regionstream:
        regions = json.load(regionstream)
    euref_data = load_and_process_euref_data()

    election_data = load_and_process_data(ADMIN_CSV, RESULTS_CSV, regions,
                                          euref_data)
    signature_count, petition_timestamp, constituency_data = load_petition_data(petition_file)
    constituency_total = sum([z for z in constituency_data.values()])
    counter = 0
    include_all = True

    sig_above_margin = 0
    pro_leave_sig_above_margin = 0
    for conres in election_data:
        ons_code = conres.constituency.ons_code
        if constituency_data[ons_code] > conres.winning_margin:
            sig_above_margin += 1
            if euref_data[ons_code].leave_pc > 50.0:
                pro_leave_sig_above_margin += 1

    if html_output:
        html_header(output_function, embed)
        sub_header(output_function, petition_timestamp, signature_count,
                   constituency_total, sig_above_margin, pro_leave_sig_above_margin)

        for i, conres in enumerate(election_data, 1):
            margin = conres.winning_margin
            ons_code = conres.constituency.ons_code
            sigs = constituency_data[ons_code]
            leave_pc = '%2d%%%s'  % (
                euref_data[ons_code].leave_pc,
                '&nbsp;' if euref_data[ons_code].known_result else '*')
            slug_party = slugify(conres.winning_party)
            # output_function(slug_party)
            #margin_text = '%sGE2017 Winning margin: %5d votes%s   ' % \
            #              (PARTY_COLOURS[slug_party], margin, COLORAMA_RESET)

            if sigs > margin or include_all:
                cells = []
                counter += 1
                cells.append(('numeric', '%s' % (counter)))
                cells.append(('', conres.constituency.name))

                if euref_data[ons_code].leave_pc >= 55.0:
                    kls = 'voted-leave-55'
                elif euref_data[ons_code].leave_pc >= 50.0:
                    kls = 'voted-leave-50'
                elif euref_data[ons_code].leave_pc >= 45.0:
                    kls = 'voted-leave-45'
                else:
                    kls = ''
                cells.append(('numeric ' + kls, leave_pc))

                cells.append(('party-%s numeric' % slug_party, '%d' % margin))


                cells.append(('numeric', '%s' % sigs))
                cells.append(('numeric', '%.1f%%' % (100 * sigs / conres.constituency.electorate)))
                ratio = (100 * sigs / margin)
                if ratio >= 100:
                    ratio_class = 'threshold-100'
                elif ratio >= 90:
                    ratio_class = 'threshold-90'
                elif ratio >= 80:
                    ratio_class = 'threshold-80'
                elif ratio >= 70:
                    ratio_class = 'threshold-70'
                elif ratio >= 50:
                    ratio_class = 'threshold-60'
                elif ratio >= 50:
                    ratio_class = 'threshold-50'
                else:
                    ratio_class = ''
                cells.append(('numeric %s' % (ratio_class), '%d%%' % ratio))

                output_function('<tr>%s</tr>' % ''.join(['<td class="%s">%s</td>' % z for z in cells]))

        output_function('''</table></body>\n</html>\n''')

    else:
        output_function('Based on petition data at %s (%d signatures)' % (petition_timestamp,
                                                                signature_count))
        output_function('Asterisked vote leave percentages are estimates - see %s' %
              EUREF_VOTES_BY_CONSTITUENCY_SHORT_URL)

        for i, conres in enumerate(election_data, 1):
            margin = conres.winning_margin
            ons_code = conres.constituency.ons_code
            sigs = constituency_data[ons_code]
            leave_pc = '%s%2d%%%s%s'  % (
                Back.MAGENTA if euref_data[ons_code].leave_pc >= 50.0 else '',
                euref_data[ons_code].leave_pc,
                ' ' if euref_data[ons_code].known_result else '*',
                COLORAMA_RESET)
            slug_party = slugify(conres.winning_party)
            # output_function(slug_party)
            margin_text = '%sGE2017 Winning margin: %5d votes%s   ' % \
                          (PARTY_COLOURS[slug_party], margin, COLORAMA_RESET)
            if sigs > margin or include_all:
                counter += 1
                output_function('%3d. %-45s : Voted leave: %s    %s    Current signatures: %5d' %
                      (counter, conres.constituency.name, leave_pc, margin_text, sigs))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        petition_file = sys.argv[1]
    else:
        # petition_file = DEFAULT_PETITION_FILE
        petition_file, _ = check_latest_petition_data()
    process(petition_file, True)



