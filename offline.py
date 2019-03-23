import webapp2


# from google.appengine.api import taskqueue
# from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from grab_latest_petition_data import DOWNLOAD_URL

DOWNLOAD_KEY = '241584'
DOWNLOAD_CACHE_TIME = 60 * 5


def get_latest():
    # Do we need to set deadline?
    result = urlfetch.fetch(DOWNLOAD_URL)
    if result.status_code == 200:
        memcache.set(DOWNLOAD_KEY, result.content, time=DOWNLOAD_CACHE_TIME)
        return result.content
    else:
        logging.error('Received %s response when getting %s' %
                      (result.status_code, DOWNLOAD_URL))
    return False

class GetLatestJSON(webapp2.RequestHandler):
    def get(self):
        try:
            get_latest()
        except Exception as err:
            logging.error('Exception %s thrown when getting %s' %
                          (result.err, DOWNLOAD_URL))


app = webapp2.WSGIApplication(
    [
      ('/Offline/getLatestJSON', GetLatestJSON)
    ], debug=True)
