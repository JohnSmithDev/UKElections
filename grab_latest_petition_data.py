#!/usr/bin/env python3

from glob import glob
import os
import pdb
import sys
# from datetime import time
import time

import requests

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'source_data')
MIN_FRESHNESS = 10 * 60 # i.e 10 minutes
FILE_PATTERN = '241584*.json'

DOWNLOAD_URL = 'https://petition.parliament.uk/petitions/241584.json'

def check_latest_petition_data():
    extant_files = glob(os.path.join(DOWNLOAD_DIR, FILE_PATTERN))
    names_and_timestamps = [(z, os.stat(z).st_ctime) for z in extant_files]
    return sorted(names_and_timestamps, key=lambda z: z[1], reverse=True)[0]

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
    print('Newest file is %d, epoch=%d, diff=%d' % (newest_timestamp, epoch,
                                                    epoch-newest_timestamp))
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
