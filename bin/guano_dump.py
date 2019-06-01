#!/usr/bin/env python
"""
Print the GUANO metadata found in a file or files.

usage::

    $> guano_dump.py [--strict] WAVFILE...
"""

from __future__ import print_function

import sys
import os
import os.path

from guano import GuanoFile


def dump(fname, strict=False):
    print()
    print(fname)
    gfile = GuanoFile(fname, strict=strict)
    print(gfile.to_string())


if __name__ == '__main__':
    from glob import glob
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\t%(levelname)s\t%(message)s')

    if len(sys.argv) < 2:
        print('usage: %s [--strict] FILE...' % os.path.basename(sys.argv[0]), file=sys.stderr)
        sys.exit(2)

    if os.name == 'nt' and '*' in sys.argv[1]:
        fnames = glob(sys.argv[1])
    else:
        fnames = sys.argv[1:]

    strict = False
    if '--strict' in fnames:
        fnames.remove('--strict')
        strict = True

    for fname in fnames:
        if os.path.isdir(fname):
            for subfname in glob(os.path.join(fname, '*.[Ww][Aa][Vv]')):
                dump(subfname, strict=strict)
        else:
            dump(fname, strict=strict)
