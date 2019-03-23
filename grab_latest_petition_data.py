#!/usr/bin/env python3

from glob import glob
import json
import logging
import os
import pdb
import sys
from datetime import datetime
import time

try:
    import requests
except ImportError:
    pass # Temp hack for GAE

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'source_data')
MIN_FRESHNESS = 10 * 60 # i.e 10 minutes
FILE_PATTERN = '241584*.json'

DOWNLOAD_URL = 'https://petition.parliament.uk/petitions/241584.json'



def extract_epoch(json_file, rogue_value=None):
    """
    Extract the updated_at value from petition JSON and convert to epoch
    time.
    """
    try:
        with open(json_file) as inputstream:
            petition_data = json.load(inputstream)
            main_attributes = petition_data['data']['attributes']
            ts = main_attributes['updated_at']
            dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%fZ')
            # Python 3 supports .timestamp() - although beware it returns float -
            # but we have to support Python 2
            return int((dt - datetime(1970,1,1)).total_seconds())
    except KeyError:
        return rogue_value

def check_latest_petition_data(use_file_timestamps=True):
    """
    use_file_timestamps is (probably) quicker, but it seems we can't rely on
    it on GAE, so otherwise parse the files and extract the timestamp from
    within.  That's theoretically better as it should give an indication of
    when exactly the data was generated, but I'd seen cases where the data
    hadn't been updated (esp. the constituency stuff but the timestamps had).

    NB: You should use the default behaviour if determining whether it is time
    to periodically download new data - otherwise you'll be downloading every
    single time if the data stops updating.  The JSON-extraction variant is
    intended for use when determining what is the freshest data of the files
    you've already downloaded.
    """
    extant_files = glob(os.path.join(DOWNLOAD_DIR, FILE_PATTERN))
    logging.warning('%d petition data files found' % (len(extant_files)))

    if use_file_timestamps:
        names_and_timestamps = [(z, os.stat(z).st_ctime) for z in extant_files]
    else:
        names_and_timestamps = [(z, extract_epoch(z)) for z in extant_files]

    freshest = sorted(names_and_timestamps, key=lambda z: z[1], reverse=True)[0]
    logging.warning('%s is the freshest file, timestamp=%d' % (freshest))
    return freshest

def die_horribly(txt):
    if txt:
        print(txt)
        error_filename = os.path.join(DOWNLOAD_DIR, 'petition_failure.txt')
        with open(error_filename, 'w') as errorstream:
            errorstream.write('%s\n' % (txt))
    sys.exit(1)

if __name__ == '__main__':

    newest_file, newest_timestamp = check_latest_petition_data()
    epoch = time.time()
    print('Newest file is %s / %d, epoch=%d, diff=%d' %
          (newest_file, newest_timestamp, epoch, epoch-newest_timestamp))

    if epoch-newest_timestamp < MIN_FRESHNESS:
        print('Not yet time to grab a new file (%d)' % (newest_timestamp))
        sys.exit(1) # This shouldn't uploaded the failure file
    try:
        req = requests.get(DOWNLOAD_URL)
        # pdb.set_trace()
        if req.status_code < 300:
            new_name = os.path.join(DOWNLOAD_DIR, '241584_AsAt%d.json' % (epoch))
            with open(new_name, 'w') as outputstream:
                outputstream.write(req.text)
                print('Success! (%d bytes saved)' % (len(req.text)))
        else:
            die_horribly('Failed to get latest file at %d -  HTTP response %s' %
                         (epoch, req.status_code))

    except Exception as err:
        die_horribly('Failed to get latest file at %d - Error: %s' %
                     (epoch, err))
