#!/usr/bin/env python3

import json
import pdb
import os
import re
import sys


from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify

def output_file(output, filename):
    with open(filename) as copystream:
        data = copystream.read()
        output.write(data)


def output_svg(out, data):
    out.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
     width="3600" height="1600"
     id="election">
''')
    out.write('''<style type="text/css">
    <![CDATA[
      .constituency {
        stroke: black;
        stroke-width: 1;
        fill: lightgrey;
      }
    ''')
    with open('general_colours.css') as copystream:
        data = copystream.read()
        out.write(data)
    out.write(']]>\n  </style>\n')


    output_file(out, 'statictext.svg')


    MARGIN = 10
    COLUMN_WIDTH=5
    Y_FACTOR = 100
    TOTAL_HEIGHT = 1600
    COUNTRY_KEY_HEIGHT = 50
    REGION_KEY_HEIGHT = 50
    CONSTITUENCY_Y_OFFSET = TOTAL_HEIGHT - MARGIN - COUNTRY_KEY_HEIGHT - \
                            REGION_KEY_HEIGHT - MARGIN

    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.winning_margin)):
    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.constituency.electorate)):
    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.winning_result.valid_votes)):
    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.margin_pc)):
    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.constituency.country_and_region)):
    # for i, conres in enumerate(sorted(election_data, key=lambda z: z.winning_party)):
    for i, conres in enumerate(sorted(election_data, key=lambda z: z.constituency.euref.leave_pc)):
        con = conres.constituency
        slugified_country = slugify(con.country)
        x_offset = MARGIN + (i * COLUMN_WIDTH)
        height = int(con.electorate / Y_FACTOR)
        y_offset = CONSTITUENCY_Y_OFFSET - height

        out.write(f'<rect x="{x_offset}" y="{y_offset}" '
                  f'width="{COLUMN_WIDTH}" height="{height}" '
                  f'class="constituency" '
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
                      f'class="result party-{slugified_party}" />\n')


    out.write('<script type="text/ecmascript">\n<![CDATA[\n')
    output_file(out, 'election_bars.js')
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

    with open('test.svg', 'w') as output_stream:
        output_svg(output_stream, election_data)
