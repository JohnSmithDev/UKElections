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

# Python2
import webapp2
from google.appengine.api import memcache

# Python3
# [START gae_python37_app]
# from flask import Flask, request, Response


import logging

from revoke_comparison import process
from grab_latest_petition_data import check_latest_petition_data

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
    buf = []
    def add_to_buffer(txt):
        buf.append(txt.decode('iso-8859-1'))

    petition_file, _ = check_latest_petition_data()
    process(petition_file, html_output=True, include_all=True,
            output_function=add_to_buffer, embed=False)

    return separator.join(buf)
    # return "hello: %d" % (len(buf))

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(generate_content())
        # self.response.write("hello")

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

