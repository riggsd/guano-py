#!/usr/bin/env python
"""
"Disperse" files by moving them into folders according to their species label.

The `Species Manual ID` field will be preferred over `Species Auto ID`.

usage::

    $> disperse.py [--copy] ROOTDIR
"""

# TODO: distinguish between Manual / Auto ID; un-disperse; recursive

from __future__ import print_function

import os
import os.path
from glob import glob
import shutil

import guano


def get_species(fname):
    """Get the species label from a GUANO file, or `None`. Prefer `Manual ID` over 'Auto ID'."""
    try:
        f = guano.GuanoFile(fname)
    except ValueError:
        return None

    species = f.get('Species Manual ID', None)
    return species if species else f.get('Species Auto ID', None)


def disperse(rootdir, copy=False, destination_root=None):
    """
    Disperse GUANO .wav files into folders by their species label.

    :param str rootdir:  the root directory where we search for GUANO files
    :param bool copy:    whether we should *copy* or *move* (default) files
    :param str destination_root:  optional destination directory where files are output
    """
    for fname in glob(os.path.join(rootdir, '*.wav')):
        species = get_species(fname)
        if not species:
            print('Skipping file without species %s .' % fname)
            continue
        destination = os.path.join(destination_root or rootdir, species)
        if not os.path.isdir(destination):
            print('Creating directory %s ...' % destination)
            os.mkdir(destination)
        new_fname = os.path.join(destination, os.path.basename(fname))
        print('%sing %s -> %s ...' % ('copy' if copy else 'mov', fname, new_fname))
        if copy:
            shutil.copy2(fname, new_fname)
        else:
            os.rename(fname, new_fname)


def main():
    """Commandline interface"""
    import argparse
    parser = argparse.ArgumentParser(description='Disperse files to folders by their species field')
    parser.add_argument('-c', '--copy', action='store_true', help='Copy files rather than moving them')
    parser.add_argument('rootdir')
    args = parser.parse_args()
    disperse(args.rootdir, copy=args.copy)


if __name__ == '__main__':
    main()
