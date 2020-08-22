#!/usr/bin/env python3
"""
Output multiple SVG (stacked) bar charts of all constituencies, sorted by
various criteria.
"""

import json
import pdb
import os
import re
import sys

from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify, output_file
from settings import (INCLUDES_DIR, OUTPUT_DIR, STATIC_DIR)
from euref_ge_comparison import EnhancedConstituencyResult


PROJECT = 'ge_constituency_bar_chart'

def XXX_output_file(output, filename):
    with open(filename) as copystream:
        data = copystream.read()
        output.write(data)

OVERALL_WIDTH = 3600
OVERALL_HEIGHT = 1600

DEBUG_MODE = True

SORT_OPTIONS = {
    # General constituency properties that (largely) don't change
    'by_electorate': lambda z: z.constituency.electorate,
    'by_region': lambda z: z.constituency.country_and_region,

    # GE related
    'by_turnout': lambda z: z.constituency.valid_votes,
    'by_turnout_pc': lambda z: z.turnout_pc,
    'by_winning_margin': lambda z: z.winning_margin,
    'by_winner_votes': lambda z: z.winning_result.valid_votes,
    'by_winning_margin_pc': lambda z: z.margin_pc,

    # EURef related
    'by_leave_pc': lambda z: z.constituency.euref.leave_pc
    }

def output_svg(out, data, sort_method='by_region'):
    out.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
     width="{OVERALL_WIDTH}" height="{OVERALL_HEIGHT}"
     id="election-bars" class="js-disabled">
''')

    OUTDATED = """
    out.write('''<style type="text/css">
    <![CDATA[
      .constituency {
        stroke: black;
        stroke-width: 1;
        fill: lightgrey;
      }
    ''')
    with open(os.path.join(STATIC_DIR, 'party_and_region_colours.css')) as copystream:
        data = copystream.read()
        out.write(data)
    out.write(']]>\n  </style>\n')
    """

    out.write('''<style type="text/css">\n<![CDATA[\n''')
    output_file(out, os.path.join(STATIC_DIR, 'party_and_region_colours.css'))
    output_file(out, os.path.join(STATIC_DIR, 'misc.css'))
    output_file(out, os.path.join(STATIC_DIR, 'euref_ge_comparison.css'))
    out.write(']]>\n  </style>\n')

    if DEBUG_MODE:
        out.write(f'''<rect x="3" y="3" width="{OVERALL_WIDTH-10}" height="{OVERALL_HEIGHT-10}"
        class="debug2" />''')

    output_file(out, os.path.join(INCLUDES_DIR, 'ge_constituency_bar_chart_static.svg'))

    out.write(f'<text x="50" y="200">{sort_method}</text>\n')


    MARGIN = 10
    COLUMN_WIDTH=5
    Y_FACTOR = 100
    TOTAL_HEIGHT = 1600
    COUNTRY_KEY_HEIGHT = 50
    REGION_KEY_HEIGHT = 50
    CONSTITUENCY_Y_OFFSET = TOTAL_HEIGHT - MARGIN - COUNTRY_KEY_HEIGHT - \
                            REGION_KEY_HEIGHT - MARGIN

    out.write('<g id="datapoints">\n')
    for i, conres in enumerate(sorted(election_data, key=SORT_OPTIONS[sort_method])):
        ecr = EnhancedConstituencyResult(conres)
        con = conres.constituency
        slugified_country = slugify(con.country)
        x_offset = MARGIN + (i * COLUMN_WIDTH)
        height = int(con.electorate / Y_FACTOR)
        y_offset = CONSTITUENCY_Y_OFFSET - height

        out.write(f'<g class="constituency" %s>\n' % (ecr.data_attributes_string()))

        out.write(f'<rect x="{x_offset}" y="{y_offset}" '
                  f'width="{COLUMN_WIDTH}" height="{height}" '
                  f'class="constituency total-electorate" '
                  f'title="{con.name}" />\n')

        country_y_pos = CONSTITUENCY_Y_OFFSET + MARGIN
        out.write(f'<rect x="{x_offset}" y="{country_y_pos}" '
                  f'width="{COLUMN_WIDTH}" height="{COUNTRY_KEY_HEIGHT}" '
                  f'class="country-{slugified_country}" '
                  f'title="{con.name} - {con.country}" />\n')
        region_y_pos = country_y_pos + COUNTRY_KEY_HEIGHT
        if con.region:
            region_class = 'region-' + slugify(con.region)
            region_text = con.region
        else:
            region_class = 'country-' + slugified_country
            region_text = con.country
        out.write(f'<rect x="{x_offset}" y="{region_y_pos}" '
                  f'width="{COLUMN_WIDTH}" height="{REGION_KEY_HEIGHT}" '
                  f'class="{region_class}" '
                  f'title="{con.name} - {region_text}" />\n')


        party_y_offset = CONSTITUENCY_Y_OFFSET
        for res_num, res in enumerate(conres.results):
            slugified_party = slugify(res.party)
            if res_num > 1:
                slugified_party = 'loser'
            party_height = int(res.valid_votes / Y_FACTOR)
            party_y_offset -= party_height
            out.write(f'  <rect x="{x_offset}" y="{party_y_offset}" '
                      f'width="{COLUMN_WIDTH}" height="{party_height}" '
                      f'class="result constituency party-{slugified_party}" />\n')
        out.write(f'</g> <!-- end of g.constituency -->\n')

    out.write(f'</g> <!-- end of #datapoints -->\n')


    # I believe election_bars.js is a precursor to constituency_details.js,
    # that looks to be the case from looking at (a) the emacs ~ backup file and
    # (b) the embedded content in temp/test.svg.
    # Basically all it did/does was add a mouseover listener to
    # rect.constituency elements that innerHTMLed the title attribute to
    # an empty text element.
    out.write('<script type="text/ecmascript">\n<![CDATA[\n')
    # qoutput_file(out, 'election_bars.js')

    output_file(out, os.path.join(STATIC_DIR, 'constituency_details.js'))
    # output_file(out, os.path.join(STATIC_DIR, 'brexit_regions.js'))

    out.write('document.querySelector("svg").classList.remove("js-disabled");\n')
    out.write('setupConstituencyDetails("hover-details", "#datapoints g.constituency");\n');


    out.write('\n]]>\n</script>')
    out.write('</svg>\n')



if __name__ == '__main__':
    with open(os.path.join('intermediate_data', 'regions.json')) as regionstream:
        regions = json.load(regionstream)
    euref_data = load_and_process_euref_data()

    election_data = load_and_process_data(ADMIN_CSV, RESULTS_CSV, regions,
                                          euref_data)

    BLAH = """
    euref_dict = dict((z.ons_code, z.leave_pc) for z in euref_data)
    for res in election_data:
        try:
            res.leave_pc = euref_dict[res.constituency.ons_code]
        except KeyError as err:
            print(err)
            pdb.set_trace()
    """


    for sort_method in SORT_OPTIONS.keys():
        output_filename = os.path.join('output', '%s_%s.svg' % (PROJECT, sort_method))
        with open(output_filename, 'w') as output_stream:
            output_svg(output_stream, election_data, sort_method=sort_method)
