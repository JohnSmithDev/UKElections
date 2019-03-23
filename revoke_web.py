#!/usr/bin/env python
"""
Web/HTML specific stuff for the revoke report
"""
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
