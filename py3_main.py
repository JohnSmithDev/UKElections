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
# import webapp2
# from google.appengine.api import memcache

# [START gae_python37_app]
from flask import Flask, request, Response


import logging


from revoke_comparison import process

app = Flask(__name__)




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


PYTHON2 = """
class MainPage(webapp2.RequestHandler):
    def get(self):
        test_text = load_from_file('README.md')
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(get_content('hello world'))
        # self.response.write(test_text)

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
"""

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    # return 'Hello World! (Python3/Flask)'
    test_text = load_from_file('html_output/test.html')
    return Response(test_text)



if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
