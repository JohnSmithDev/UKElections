#!/usr/bin/env python3
"""
Churn through a bunch of markup files obtained from Wikipedia pages and
turn them into a JSON file mapping English regions to a list of constituencies.

Alternatively you can import/call extract_regions() to dynamically load and
process the source files to the same structure.

Wikipedia pages in question are the likes of:
  https://en.wikipedia.org/wiki/List_of_Parliamentary_constituencies_in_London
as found at
  https://en.wikipedia.org/wiki/Category:Lists_of_United_Kingdom_Parliamentary_constituencies_in_England

I'm sure this data must be available online in a directly usable format, but
my Google-fu was unable to find it.  (Ideally such data would use OPS
constituency codes, which should be less prone to inconsistencies compared to
constituency names.)
"""

import glob
import os
# import pdb
import re
import sys
import json


DEFAULT_WIKI_FILES = glob.glob(os.path.join('source_data', '*.wiki'))

def extract_label_from_md_link(txt):
    # pdb.set_trace()
    stuff = re.search('\[\[(.*)\|(.*)\]\]', txt)
    if stuff:
        return stuff.group(2)
    else:
        return txt

def remove_unwanted_suffix(txt):
    if txt.endswith(' BC') or txt.endswith(' CC'):
        return txt[:-3]
    else:
        return txt

def extract_region_name(txt):
    stuff =  re.search('\|\s*name\s*=\s*(.*)\s*$', txt)
    region = stuff.group(1)
    if region.endswith(' England'):
        # Hmm, this is OK for "North West England", but is silly for
        # "East of England"
        region = region[:-8]
    if region.lower().endswith(' of'):
        # This addresses the aforementioned issue, but maybe not optimally?
        region = region[:-3]
    return region

def extract_region(wiki_file):
    in_constituencies = False
    in_table = False

    row_element = None

    in_infobox = False
    # london file doesn't have an infobox, so use this horrible hack :-(
    # TODO (maybe): Derive it from the content of the file if possible?
    region_name = re.sub('\.Wiki$', '', os.path.basename(wiki_file).title())

    constituencies = []

    for line_num, raw_line in enumerate(open(wiki_file)):
        line = raw_line.strip()
        if line.lower().startswith('{{infobox'):
            in_infobox = True
        elif in_infobox and line.startswith('}}'):
            in_infobox = False
        elif in_infobox and re.search('\|\s*name\s*=', line):
            region_name = extract_region_name(line)
        elif line.lower() == '==constituencies==':
            in_constituencies = True
        elif line.startswith('='):
            in_constituencies = False
        elif line.startswith('{|'):
            in_table = True
        elif line.startswith('|}'):
            in_table = False
        elif line == '|-' and in_table:
            row_element = 0
        elif line.startswith('!'):
            pass # ignore header line
        elif line == '':
            pass # Ignore blank line
        elif in_constituencies and in_table and row_element is not None:
            row_element += 1
            if row_element == 1:
                con_name = remove_unwanted_suffix(extract_label_from_md_link(line))
                constituencies.append(con_name)
                # print('%s %s' % (region_name, con_name))
    return region_name, constituencies

def extract_regions(wiki_files=None):
    if not wiki_files:
        wiki_files = DEFAULT_WIKI_FILES
    region2cons = {}
    for f in wiki_files:
        region, cons = extract_region(f)
        region2cons[region] = cons
    return region2cons

if __name__ == '__main__':
    if len(sys.argv) == 1:
        files = DEFAULT_WIKI_FILES
    else:
        files = sys.argv[1:]
    region2cons = extract_regions(files)
    with open(os.path.join('intermediate_data', 'regions.json'), 'w') as output:
        json.dump(region2cons, output)
