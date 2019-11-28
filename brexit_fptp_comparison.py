#!/usr/bin/env python3
"""
Output a scatter plot cross referencing GE2017 results with EU Ref results
at the constituency and region levels.


"""

import json
import pdb
import os
import re
import sys


from ec_data_reader import load_and_process_data, ADMIN_CSV, RESULTS_CSV
from euref_data_reader import load_and_process_euref_data
from misc import slugify, output_file

INCLUDES_DIR = os.path.join(os.path.dirname(__file__), 'includes')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

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

# OVERALL_WIDTH = 1600 # Original value, although the plot width was more like 1300
OVERALL_WIDTH = 1800 # Roughly full HD (1920x1080) with ample space for scrollbars etc
OVERALL_HEIGHT = 1000 # Leave some space for browser chrome on Full HD screen


CENTRE_X = int(OVERALL_WIDTH / 2)
CENTRE_Y = int(OVERALL_HEIGHT / 2)
DOT_RADIUS = 4
DOT_DIAMETER = DOT_RADIUS * 2


def output_svg(out, data):
    out.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
     width="{OVERALL_WIDTH}" height="{OVERALL_HEIGHT}"
     id="election">
''')
    out.write('<title>Constituency results in 2017 General Election and 2016 EU Referendum</title>\n')
    out.write('<description>Scatter plot of constituency results '
              'in 2017 General Election and 2016 EU Referendum</description>\n')

    out.write('''<style type="text/css">
    <![CDATA[
      .constituency {
        stroke: black;
        stroke-width: 1;
        fill: lightgrey;
      }
    ''')
    output_file(out, os.path.join(STATIC_DIR, 'general_colours.css'))
    output_file(out, os.path.join(STATIC_DIR, 'misc.css'))
    output_file(out, os.path.join(STATIC_DIR, 'brexit_fptp.css'))
    out.write(']]>\n  </style>\n')

    # out.write(f'''<rect x="3" y="3" width="{OVERALL_WIDTH-10}" height="{OVERALL_HEIGHT-10}"
    #           class="debug2" />''')
    # out.write(f'<rect x="5" y="5" width="1590" height="990" class="debug" />')

    output_file(out, os.path.join(INCLUDES_DIR, 'brexit_fptp_static.svg'))

    # So leave covered a range of (80-20)*10 = 600 pixels (vertical)
    # and GE margin covered a range of 110*10 = 1100 pixels (vertical)
    # so increase from 10 to 15 now that we are using Full HD(ish) resolution
    # (15 is just a bit too big)
    LEAVE_PC_SCALE = 14
    MARGIN_PC_SCALE = 14
    LEAVE_PC_RANGE = (20,80) # inclusive range
    # NB: in GE2017, there are 3 Labour constituencies with a margin between
    # 50 and 55%, so watch out in future in case this goes higher.  (No Tory
    # constituency goes above 40%)
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
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    else:
        output_filename = 'brexit_fptp.svg'

    with open(os.path.join('intermediate_data', 'regions.json')) as regionstream:
        regions = json.load(regionstream)
    euref_data = load_and_process_euref_data()

    election_data = load_and_process_data(ADMIN_CSV, RESULTS_CSV, regions,
                                          euref_data)

    with open(output_filename, 'w') as output_stream:
        output_svg(output_stream, election_data)
