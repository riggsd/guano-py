#!/usr/bin/env python
"""
Print the GUANO metadata found in a file or files.

usage::

    $> guano_dump.py WAVFILE...
"""

from __future__ import print_function

import sys
import os
import os.path

from guano import GuanoFile


def dump(fname):
    print()
    print(fname)
    gfile = GuanoFile(fname)
    print(gfile.to_string())


if __name__ == '__main__':
    from glob import glob

    if len(sys.argv) < 2:
        print('usage: %s FILE...' % os.path.basename(sys.argv[0]), file=sys.stderr)
        sys.exit(2)

    if os.name == 'nt' and '*' in sys.argv[1]:
        fnames = glob(sys.argv[1])
    else:
        fnames = sys.argv[1:]

    for fname in fnames:
        dump(fname)
