#!/usr/bin/env python2
"""
Print the GUANO metadata from a file or files.

usage: guano_dump.py WAVFILE...
"""

import sys
import os
import os.path

from guano import GuanoFile


def dump(fname):
    print
    print fname
    gfile = GuanoFile(fname)
    print gfile._as_string()


if __name__ == '__main__':
    from glob import glob

    if len(sys.argv) < 2:
        print >> sys.stderr, 'usage: %s FILE...' % os.path.basename(sys.argv[0])
        sys.exit(2)

    if os.name == 'nt' and '*' in sys.argv[1]:
        fnames = glob(sys.argv[1])
    else:
        fnames = sys.argv[1:]

    for fname in fnames:
        dump(fname)
