# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json

# Python2
import webapp2
from google.appengine.api import memcache

# Python3
# [START gae_python37_app]
# from flask import Flask, request, Response


import logging

from revoke_comparison import process
from grab_latest_petition_data import check_latest_petition_data

from offline import DOWNLOAD_KEY, get_latest


PAGE_KEY = 'main_page'
PAGE_CACHE_TIME = 60

# app = Flask(__name__)




def get_content(stuff):
    return """<!DOCTYPE html><html><head>
<link rel="stylesheet" type="text/css" href="/static/table_colours.css" />
<script src="/static/sortable.js">
</script>
</head>
<body>%s</body></html>\n""" % (stuff)


def load_from_file(filename):
    with open(filename, mode='rb') as inputstream:
        data = inputstream.read()
    return data


def generate_content(separator='\n'):
    content = memcache.get(PAGE_KEY)
    if content:
        return content
    logging.warning('Did not find page content %s in memcache - regenerating' % (PAGE_KEY))

    buf = []
    def add_to_buffer(txt):
        buf.append(txt.decode('iso-8859-1'))

    raw_string_data = memcache.get(DOWNLOAD_KEY)
    if raw_string_data:
        logging.warning("loaded %s (%d bytes) from memcache" % (DOWNLOAD_KEY,
                                                                len(raw_string_data)))
        petition_data = json.loads(raw_string_data)
    else:
        logging.warning('Unable to get data %s from memcache: %s, getting it manually' %
                        (DOWNLOAD_KEY, err))
        petition_data = json.loads(get_latest())
        # petition_file, _ = check_latest_petition_data(use_file_timestamps=False)

    process(petition_data=petition_data, html_output=True, include_all=True,
            output_function=add_to_buffer, embed=False)

    content =  separator.join(buf)
    memcache.set(PAGE_KEY, content, time=PAGE_CACHE_TIME)
    return content



class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.headers['Cache-Control'] = 'max-age=%d, public' % (PAGE_CACHE_TIME)
        self.response.write(generate_content())
        # self.response.write("hello")

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

