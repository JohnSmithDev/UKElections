#!/usr/bin/env python3

import json
import pdb
import os
import re
import sys


from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify


RULING_PARTIES = ('Conservative', 'DUP', 'Speaker')
ABSOLUTE_MARGIN_PC = False

MARGIN = 10
COLUMN_WIDTH=5
Y_FACTOR = 100
TOTAL_HEIGHT = 800
COUNTRY_KEY_HEIGHT = 50
REGION_KEY_HEIGHT = 5
CONSTITUENCY_Y_OFFSET = TOTAL_HEIGHT - MARGIN - COUNTRY_KEY_HEIGHT - \
                            REGION_KEY_HEIGHT - MARGIN

CENTRE_X = 650
CENTRE_Y = 380
DOT_RADIUS = 4
DOT_DIAMETER = DOT_RADIUS * 2


def output_file(output, filename):
    output.flush()
    with open(filename, mode='rb') as copystream:
        data = copystream.read()
        output.buffer.write(data)


def output_svg(out, data):
    out.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
     width="1600" height="1000"
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
    output_file(out, 'general_colours.css')
    output_file(out, 'misc.css')
    output_file(out, 'brexit_fptp.css')
    out.write(']]>\n  </style>\n')


    output_file(out, 'brexit_fptp_static.svg')

    LEAVE_PC_SCALE = 10
    MARGIN_PC_SCALE = 10
    LEAVE_PC_RANGE = (20,80) # inclusive range
    if ABSOLUTE_MARGIN_PC:
        MARGIN_PC_RANGE = (0,55) # inclusive range
    else:
        MARGIN_PC_RANGE = (-55, 55) # inclusive range

    def calculate_fptp_margin_offset(val):
        return CENTRE_X + (val * MARGIN_PC_SCALE)
    def calculate_leave_pc_offset(val):
        return CENTRE_Y - ((val-50) * LEAVE_PC_SCALE)

    ### Horizontal grid lines and Y axis
    x_start = calculate_fptp_margin_offset(MARGIN_PC_RANGE[0])
    x_end = calculate_fptp_margin_offset(MARGIN_PC_RANGE[1])
    for val in range(LEAVE_PC_RANGE[0], LEAVE_PC_RANGE[1]+1):
        y_offset = calculate_leave_pc_offset(val)
        if val % 5 != 0:
            css_class = 'grid-line-light'
        else:
            if val == 50:
                css_class = 'grid-line-strong'
            else:
                css_class = 'grid-line'

            out.write(f'<text x="{x_start-2}" y="{y_offset}" class="y-axis-label">'
                      f'{val}%</text>')
        out.write(f'<line x1="{x_start}" y1="{y_offset}" '
                  f'x2="{x_end}" y2="{y_offset}" class="{css_class}" />\n')

    out.write(f'<text x="{x_start-30}" y="{y_offset}" class="y-axis-label">'
                      f'Voted leave</text>')

    ### Vertical grid lines and X axis labels
    y_start = calculate_leave_pc_offset(LEAVE_PC_RANGE[0])
    y_end = calculate_leave_pc_offset(LEAVE_PC_RANGE[1])
    for val in range(MARGIN_PC_RANGE[0], MARGIN_PC_RANGE[1]+1):
        x_offset = calculate_fptp_margin_offset(val)
        if val % 5 != 0:
            css_class = 'grid-line-light'
        else:
            out.write(f'<text x="{x_offset}" y="{y_start+10}" class="x-axis-label">'
                      f'{val}%</text>')
            if not ABSOLUTE_MARGIN_PC and val == 0:
                css_class = 'grid-line-strong'
            else:
                css_class = 'grid-line'

        out.write(f'<line x1="{x_offset}" y1="{y_start}" '
                  f'x2="{x_offset}" y2="{y_end}" class="{css_class}" />\n')

    out.write(f'<text x="{x_offset+70}" y="{y_start+10}" class="y-axis-label">'
                      f'GE2017 Margin</text>')

    for i, conres in enumerate(election_data):
        con = conres.constituency
        slugified_country = slugify(con.country)
        winner = slugify(conres.winning_party)
        runner_up = slugify(conres.results[1].party)

        y_offset = calculate_leave_pc_offset(con.euref.leave_pc)

        winning_margin = conres.margin_pc
        if not ABSOLUTE_MARGIN_PC and conres.winning_party not in RULING_PARTIES:
            winning_margin = -conres.margin_pc
        x_offset = calculate_fptp_margin_offset(winning_margin)

        if con.euref.known_result:
            x_offset -= DOT_RADIUS
            y_offset -= DOT_RADIUS
            out.write(f'<rect x="{x_offset}" y="{y_offset}" '
                      f'width="{DOT_DIAMETER}" height="{DOT_DIAMETER}" ')
        else:
            out.write(f'<circle cx="{x_offset}" cy="{y_offset}" '
                      f'r="{DOT_RADIUS}" ')
        out.write(f'class="constituency party-{winner} second-place-{runner_up}" '
                  f'title="{con.name} - {con.country}" />\n')

    out.write('<script type="text/ecmascript">\n<![CDATA[\n')
    output_file(out, 'constituency_details.js')

    out.write('setupConstituencyDetails("constituency-details", ".constituency");\n');
    out.write('\n]]>\n</script>')
    out.write('</svg>\n')



if __name__ == '__main__':
    with open(os.path.join('intermediate_data', 'regions.json')) as regionstream:
        regions = json.load(regionstream)
    euref_data = load_and_process_euref_data()

    election_data = load_and_process_data(ADMIN_CSV, RESULTS_CSV, regions,
                                          euref_data)

    with open('brexit_fptp.svg', 'w') as output_stream:
        output_svg(output_stream, election_data)
