#!/usr/bin/env python
"""
"Disperse" files by moving them into folders according to their species label.

The `Species Manual ID` field will be preferred over `Species Auto ID`.

usage::

    $> disperse.py ROOTDIR
"""

# TODO: add options to copy vs move; distinguish between Manual / Auto ID; un-disperse

from __future__ import print_function

import os
import os.path
from glob import glob

import guano


def get_species(fname):
    """Get the species label from a GUANO file, or `None`. Prefer `Manual ID` over 'Auto ID'."""
    try:
        f = guano.GuanoFile(fname)
    except ValueError:
        return None

    species = f.get('Species Manual ID', None)
    return species if species else f.get('Species Auto ID', None)


def disperse(rootdir):
    """Disperse GUANO .wav files into folders by their species label."""
    for fname in glob(os.path.join(rootdir, '*.wav')):
        species = get_species(fname)
        if not species:
            print('Skipping file without species %s .' % fname)
            continue
        destination = os.path.join(rootdir, species)
        if not os.path.isdir(destination):
            print('Creating directory %s ...' % destination)
            os.mkdir(destination)
        new_fname = os.path.join(destination, os.path.basename(fname))
        print('%s -> %s ...' % (fname, new_fname))
        os.rename(fname, new_fname)


def main():
    """Commandline interface"""
    import argparse
    parser = argparse.ArgumentParser(description='Disperse files to folders by species field')
    parser.add_argument('rootdir')
    args = parser.parse_args()
    disperse(args.rootdir)


if __name__ == '__main__':
    main()
