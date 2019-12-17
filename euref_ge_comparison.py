#!/usr/bin/env python3
"""
Output a scatter plot cross referencing GE2017 results with EU Ref results
at the constituency and region levels.


"""

from decimal import Decimal
import json
import pdb
import os
import re
import sys


from ec_data_reader import (load_and_process_data, load_and_process_data_2019,
                            ADMIN_CSV, RESULTS_CSV,
                            load_region_data)
from euref_data_reader import load_and_process_euref_data
from misc import slugify, output_file
from helpers import short_region

from settings import (INCLUDES_DIR, OUTPUT_DIR, STATIC_DIR)
from ge_config import GENERAL_ELECTIONS

DEBUG_MODE = False

PROJECT = 'euref_ge_comparison'

RULING_PARTIES = ('Conservative', 'DUP', 'Speaker') # TODO: remove refs to this
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
OVERALL_HEIGHT = 950 # Leave some space for browser chrome on Full HD screen


CENTRE_X = int(OVERALL_WIDTH / 2) - 70 # Give more space for legend etc on RHS
CENTRE_Y = int(OVERALL_HEIGHT / 2) + 30 # Give more space under title for interactive info
DOT_RADIUS = 4
DOT_DIAMETER = DOT_RADIUS * 2


class EnhancedConstituencyResult(object):
    """
    ConstituencyResult object with derived properties that are helpful when
    outputting an SVG
    """

    def __init__(self, conres, ruling_parties=RULING_PARTIES):
        self.conres = conres
        self.con = conres.constituency
        self.winner_slug = slugify(conres.winning_party)
        self.runner_up_slug = slugify(conres.results[1].party)
        self.full_region = self.con.country_and_region
        self.region_slug = slugify(self.full_region)

        # Ensures this is populated for W, S, NI
        self.region = self.con.region or self.con.country

        self.winning_margin = conres.margin_pc
        if not ABSOLUTE_MARGIN_PC and conres.winning_party not in ruling_parties:
            self.winning_margin = -conres.margin_pc

        self.winner_votes = conres.results[0].valid_votes
        self.runner_up_votes = conres.results[1].valid_votes
        # Do all the percentage calculations in Python using Decimal to avoid
        # horrible rounding/floating-point issues in JS
        self.turnout = '%.1f' % (conres.turnout_pc)
        self.winner_pc = '%.1f' % (100 * self.winner_votes / self.con.valid_votes)
        self.runner_up_pc = '%.1f' % (100 * self.runner_up_votes / self.con.valid_votes)
        self.won_by_pc = '%.1f' % (100 * (self.winner_votes - self.runner_up_votes)
                              / self.con.valid_votes)

    def data_attributes_string(self):
        """
        Includes a title attribute as well
        """
        return f'''data-winner="{self.conres.winning_party}"
        data-winner-votes="{self.winner_votes}"
        data-winner-percent="{self.winner_pc}"
        data-runner-up="{self.conres.results[1].party}"
        data-runner-up-votes="{self.runner_up_votes}"
        data-runner-up-percent="{self.runner_up_pc}"
        data-electorate="{self.con.electorate}" data-valid-votes="{self.con.valid_votes}"
        data-turnout="{self.turnout}"
        data-won-by-percent="{self.won_by_pc}"
        data-leave-percent="{self.con.euref.leave_pc}"
        data-leave-known-figure="{'Y' if self.con.euref.known_result else 'N'}"
        title="{self.con.name}"'''

def output_svg(out, data, year, ruling_parties=RULING_PARTIES, value_map=None):
    out.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
     width="{OVERALL_WIDTH}" height="{OVERALL_HEIGHT}"
     id="election" class="js-disabled">
''')
    out.write(f'<title>Constituency results in {year} General Election and 2016 EU Referendum</title>\n')
    out.write('<description>Scatter plot of constituency results '
              f'in {year} General Election and 2016 EU Referendum</description>\n')

    out.write('''<style type="text/css">\n<![CDATA[\n''')
    output_file(out, os.path.join(STATIC_DIR, 'party_and_region_colours.css'))
    output_file(out, os.path.join(STATIC_DIR, 'misc.css'))
    output_file(out, os.path.join(STATIC_DIR, 'euref_ge_comparison.css'))
    out.write(']]>\n  </style>\n')

    if DEBUG_MODE:
        out.write(f'''<rect x="3" y="3" width="{OVERALL_WIDTH-10}" height="{OVERALL_HEIGHT-10}"
        class="debug2" />''')

    if not value_map:
        value_map = {}
    output_file(out, os.path.join(INCLUDES_DIR, 'brexit_fptp_static.svg'),
                value_map=value_map)
    # So leave covered a range of (80-20)*10 = 600 pixels (vertical)
    # and GE margin covered a range of 110*10 = 1100 pixels (vertical)
    # so increase from 10 to 15 now that we are using Full HD(ish) resolution
    # (15 is just a bit too big, as is 14 on some browsers e.g. FF
    # Update: 14 is too much for X now that I calculate GE margin properly
    LEAVE_PC_SCALE = 13
    MARGIN_PC_SCALE = 9
    LEAVE_PC_RANGE = (20,80) # inclusive range
    # NB: in GE2017, there are 3 Labour constituencies with a margin between
    # 50 and 55%, so watch out in future in case this goes higher.  (No Tory
    # constituency goes above 40%)
    # UPDATE: due to using electorate rather than valid vote, the range is more
    # like 80, not 55
    if ABSOLUTE_MARGIN_PC:
        MARGIN_PC_RANGE = (0,80) # inclusive range
    else:
        # inclusive range, we only need to ~50 for Tories, but prefer to keep
        # symmetrical
        MARGIN_PC_RANGE = (-80, 80)

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

    out.write(f'<text x="{CENTRE_X}" y="{y_start+20}" class="y-axis-label centre-aligned">'
                      f'Winning margin in General Election</text>')

    relevant_parties = set()
    regions = set()

    out.write('<g id="datapoints">\n')
    prev_region = None
    for i, conres in enumerate(sorted(election_data,
                                      key=lambda z: z.constituency.country_and_region)):
        ecr = EnhancedConstituencyResult(conres, ruling_parties=ruling_parties)

        con = conres.constituency
        winner = slugify(conres.winning_party)
        runner_up = slugify(conres.results[1].party)
        relevant_parties.update([conres.winning_party, conres.results[1].party])

        full_region = con.country_and_region
        regions.add(full_region)
        slugified_region = slugify(full_region)
        region = con.region or con.country # Ensure this is populated for W, S, NI
        if prev_region is None or slugified_region != prev_region:
            if prev_region is not None:
                out.write(f'</g> <!-- end of {prev_region} -->\n')
            out.write(f'''<g class="js-level level-{slugified_region}"
            id="region-{slugified_region}"
            data-country="{con.country}" data-region="{region}">\n''')
            prev_region = slugified_region

        y_offset = calculate_leave_pc_offset(con.euref.leave_pc)

        winning_margin = conres.margin_pc
        if not ABSOLUTE_MARGIN_PC and conres.winning_party not in ruling_parties:
            winning_margin = -conres.margin_pc
        x_offset = Decimal('%.1f' % (calculate_fptp_margin_offset(winning_margin)))

        if con.euref.known_result:
            x_offset -= DOT_RADIUS
            y_offset -= DOT_RADIUS
            out.write(f'<rect x="{x_offset}" y="{y_offset}" '
                      f'width="{DOT_DIAMETER}" height="{DOT_DIAMETER}" ')
        else:
            out.write(f'<circle cx="{x_offset}" cy="{y_offset}" '
                      f'r="{DOT_RADIUS}" ')

        out.write(f'class="constituency party-{winner} second-place-{runner_up}"\n')
        out.write(ecr.data_attributes_string() + '/>\n')


    out.write(f'</g> <!-- end of {prev_region} -->\n')
    out.write(f'</g> <!-- end of #datapoints -->\n')

    ### Legend
    x_pos = 1575
    y_pos = 125
    line_spacing = 14
    DEFAULT_BUTTON_WIDTH = 190
    out.write('<g class="legend">\n');
    out.write(f'<text x="{x_pos}" y="{y_pos}" class="heading">Legend and filters</text>\n')

    for txt in ['Fill colour indicates winner.  Border/',
                'outline colour indicates runner-up.',
                '',
                'Square dots indicate definite known',
                'EU Referendum constituency results',
                'circles indicate estimated results',
                'as published on Parliament.uk.',
                '',
                'Click on the items below to filter',
                'on that particular party, winner,',
                'party, winner, runner-up or region.',
                ]:
        y_pos += line_spacing
        out.write(f'<text x="{x_pos}" y="{y_pos}">{txt}</text>\n')


    def output_button_with_arbitrary_content(
            out, x_offset, y_offset, line_spacing,
            svg_content,
            element_id=None, classes=None, data_attributes=None,
            width=DEFAULT_BUTTON_WIDTH, is_selected=False):

        if not classes:
            classes = []
        if not data_attributes:
            data_attributes = {}
        if is_selected:
            classes.append(' selected')
        classes.append('js-button')

        if not element_id:
            id_bit = ''
        else:
            id_bit = f'id="{element_id}"'
        class_string = ' '.join(classes)
        def data_prefixed(attribute_name):
            if not attribute_name.startswith('data-'):
                return 'data-%s' % (attribute_name)
            else:
                return attribute_name
        attribute_bits = ['%s="%s"' % (data_prefixed(k), v) for k, v in data_attributes.items()]
        attribute_string = ' '.join(attribute_bits)
        out.write(f'''<g class="{class_string}" {id_bit}
        {attribute_string}>\n''')
        out.write(f'''  <rect x="{x_offset}" y="{y_offset}" rx="{line_spacing * 0.6}"
        width="{width}" height="{line_spacing * 1.25}" />\n''')
        out.write(svg_content)
        out.write('</g>\n')

    def output_text_button(out, x_offset, y_offset, line_spacing, label,
                      element_id=None, classes=None, data_attributes=None,
                      width=DEFAULT_BUTTON_WIDTH, is_selected=False):
        # -2 is a hack to allow for descenders
        svg_bits = f'  <text x="{x_offset+10}" y="{y_offset+line_spacing-2}">{label}</text>\n'
        return output_button_with_arbitrary_content(out, x_offset, y_offset,
                                                    line_spacing, svg_bits,
                                                    element_id, classes, data_attributes,
                                                    width, is_selected)

    # y_pos += line_spacing
    for p in sorted(relevant_parties):
        p_slug = slugify(p)
        y_pos += line_spacing * 1.5
        circle_svg = f'''<circle cx="{x_pos+15}" cy="{y_pos+9}" r="4"
        class="constituency winner party-{p_slug}" />\n'''
        output_button_with_arbitrary_content(out, x_pos, y_pos, line_spacing,
                                             circle_svg,
                                             # 'js-party-filter-%s' % (p_slug),
                                             classes=['selectable-party-position'],
                                             data_attributes={'party': p_slug},
                                             width=30)
        circle_svg = f'''<circle cx="{x_pos+50}" cy="{y_pos+9}" r="4"
        class="constituency second-place second-place-{p_slug}" />\n'''
        output_button_with_arbitrary_content(out, x_pos+35, y_pos, line_spacing,
                                             circle_svg,
                                             # 'js-party-filter-%s' % (p_slug),
                                             classes=['selectable-party-position'],
                                             data_attributes={'party': p_slug},
                                             width=30)
        output_text_button(out, x_pos+70, y_pos, line_spacing, p,
                      # 'js-party-filter-%s' % (p_slug),
                      classes=['selectable-party'], data_attributes={'party': p_slug},
                           width=120)


    y_pos += 40
    out.write('<g class="hide-if-no-js">\n')
    output_text_button(out, x_pos, y_pos, line_spacing, 'All regions',
                  element_id='js-level-all', classes=['js-level-button'],
                  data_attributes={'level': 'all'}, is_selected=True)
    for region in sorted(regions):
        y_pos += line_spacing * 1.5
        slugified_region = slugify(region)
        output_text_button(out, x_pos, y_pos, line_spacing, short_region(region),
                      element_id='js-level-%s' % slugified_region,
                      classes=['js-level-button'],
                      data_attributes={'level': slugified_region})

    out.write('</g> <!-- end of hide-if-no-js -->\n')

    y_pos = 900
    output_text_button(out, x_pos, y_pos, line_spacing, 'Toggle dark mode',
                  element_id='js-dark-mode-toggle')

    out.write('</g> <!-- end of legend -->\n')

    out.write('<script type="text/ecmascript">\n<![CDATA[\n')
    output_file(out, os.path.join(STATIC_DIR, 'constituency_details.js'))
    output_file(out, os.path.join(STATIC_DIR, 'brexit_regions.js'))

    out.write('document.querySelector("svg").classList.remove("js-disabled");\n')
    out.write('setupConstituencyDetails("hover-details", "#datapoints .constituency");\n');

    out.write('\n]]>\n</script>')
    out.write('</svg>\n')




if __name__ == '__main__':
    year = None
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
            output_filename = os.path.join(OUTPUT_DIR, '%s_%d.svg' % (PROJECT, year))
        except ValueError:
            output_filename = sys.argv[1]
    else:
        output_filename = os.path.join(OUTPUT_DIR, '%s.svg' % (PROJECT))

    regions = load_region_data(add_on_countries=True)
    euref_data = load_and_process_euref_data()

    GE_YEAR = year or 2017
    ge_cfg = GENERAL_ELECTIONS[GE_YEAR]
    if year == 2019:
        election_data = load_and_process_data_2019(
            GENERAL_ELECTIONS[GE_YEAR]['constituencies_csv'],
            regions,
            euref_data)
    else:
        election_data = load_and_process_data(
            GENERAL_ELECTIONS[GE_YEAR]['constituencies_csv'],
            GENERAL_ELECTIONS[GE_YEAR]['results_csv'],
            regions,
            euref_data)


    value_map = {'ge_year': year,
                 'ge_data_credit': ge_cfg.get('data_credit', 'Electoral Commission'),
                 'ge_data_url': ge_cfg.get('data_url',
                                           'https://www.electoralcommission.org.uk/our-work/our-research/electoral-data/electoral-data-files-and-reports')
    }



    with open(output_filename, 'w') as output_stream:
        output_svg(output_stream, election_data, GE_YEAR,
                   ruling_parties=GENERAL_ELECTIONS[GE_YEAR]['ruling_parties'],
                   value_map=value_map
        )
