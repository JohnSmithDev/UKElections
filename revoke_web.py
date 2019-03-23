#!/usr/bin/env python
"""
Web/HTML specific stuff for the revoke report

This code is very clunky, but - for the time being at least - I want to be able
to:
* Not have any non-stdlib dependecies
* Be able to generate a single standalone HTML file
"""

import os
import sys


from misc import output_file


EUREF_VOTES_BY_CONSTITUENCY_URL = 'https://commonslibrary.parliament.uk/' + \
                                  'parliament-and-elections/elections-elections/' + \
                                  'brexit-votes-by-constituency/'
EUREF_VOTES_BY_CONSTITUENCY_SHORT_URL = 'http://tinyurl.com/ybnmmzz9'

def html_header(output_function, embed):
        title = '''Analysis of Revoke Article 50 petition vs General Election 2017
                     and EU Referendum results'''

        output_function('''<!DOCTYPE html>\n<html lang="en-GB">\n<head>''')

        # Not sure if this is right, but FF whinges otherwise
        output_function('<meta charset="utf-8" />\n')
        # output_file(sys.stdout, 'table_colours.css')
        # output_function('.voted-leave { background: purple; color: white; }</style>')
        if embed:
            output_function('<style>\n')
            output_file(sys.stdout, os.path.join('static', 'table_colours.css'))
            output_function('</style>\n')
        else:
            output_function('''<link rel="stylesheet" type="text/css"
                  href="/static/table_colours.css" />\n''')

        output_function('<title>%s</title>\n' % (title))
        # Do we need both twitter: and og: metatags?  Fuck knows
        output_function('''<meta name="twitter:card" content="summary_large_image"></meta>
           <meta name="twitter:site" content="@JohnMMIX"></meta>
           <meta name="twitter:creator" content="@JohnMMIX"></meta>
           <meta name="twitter:url" content="https://john-smith-test.appspot.com/"></meta>
           <meta name="twitter:description" content="Tabular real-time-ish analysis of the Revoke Article 50 petition's latest stats vs General Election 2017 and EU Referendum results"></meta>
           <meta name="twitter:image" content="https://john-smith-test.appspot.com/static/screengrab.png"></meta>


           <meta name="og:url" content="https://john-smith-test.appspot.com/"></meta>
           <meta name="og:title" content="Analysis of Revoke Article 50 petition"></meta>
           <meta name="og:description" content="Tabular real-time-ish analysis of the Revoke Article 50 petition's latest stats vs General Election 2017 and EU Referendum results"></meta>
           <meta name="og:image" content="https://john-smith-test.appspot.com/static/screengrab.png"></meta>
        ''')


        output_function('</head><body>\n')
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

        output_function('''Party colours via
<a href="https://en.wikipedia.org/wiki/2017_United_Kingdom_general_election#Full_results">Wikipedia</a>.
        Regions also via Wikipedia
(e.g. <a href="https://en.wikipedia.org/wiki/List_of_Parliamentary_constituencies_in_London">London</a>),
       but presumably they were taken from somewhere/someone else.</p>''')
        output_function('''<p><a href="https://github.com/JohnSmithDev/UKElections">Code</a>
               by <a href="https://twitter.com/JohnMMIX">John Smith</a>.
Table sorting (click on the headers) via <a href="https://www.kryogenix.org/code/browser/sorttable/">sorttable</a>.
</p>''')

        output_function('''<h2>%d constituencies have more petition signatures
        than their GE2017 winning margin, of which %d voted in favour of leaving in
        the 2016 EU Referendum</h2>''' %
              (sig_above_margin, pro_leave_sig_above_margin))


        output_function('<table class="sortable">\n<tr>\n')
        output_function('''<th></th><th>Region</th><th>Constituency</th>
        <th>Voted leave percentage</th>
        <th>GE 2017 winning # votes</th>
        <th>GE 2017 winning margin (# votes)</th>
<th>Petition signatures</th>
    <th>Percentage of electorate</th>

<th>Percentage of winning GE2017 vote</th>
<th>Petition to winning margin ratio</th>''')
