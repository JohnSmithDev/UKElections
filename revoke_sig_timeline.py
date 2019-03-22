#!/usr/bin/env python3


import os
import glob
import sys

from revoke_comparison import load_petition_data



def process_files(files):
    names_and_timestamps = sorted([(z, os.stat(z).st_ctime) for z in files],
                                  key=lambda z: z[1])

    for fn, file_ts in names_and_timestamps:
        sig_count, ts, constituency_data = load_petition_data(fn)
        constituency_total = sum([z for z in constituency_data.values()])
        print('Data at %s: Total sigs: %9d   Constituency-associated sigs: %9d   Percentage: %d%%' %
              (ts, sig_count, constituency_total, (100 * constituency_total / sig_count)))



if __name__ == '__main__':
    process_files(sys.argv[1:])
