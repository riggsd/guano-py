#!/usr/bin/env python
"""
guano_edit.py - Manipulate GUANO metadata of individual files or in bulk.

Specify GUANO fields and values, followed by a list of files which the
changes should be applied to. The values of existing fields may be
used by specifying the field as `${Fieldname}`.

Be careful to properly escape values for your shell commandline, especially
if using value templates! Study the examples below.


Examples::

    # Add NABat grid cell to all recordings under the `foo` directory
    $> guano_edit.py  "NABat|Grid Cell ID: 45678"  ~/bat_calls/foo/

    # Append additional text to the end of the existing Note text
    $> guano_edit.py  'Note: ${Note} Recorded by Dave.'  EPFU_refcall.wav


TODO::
    * Ensure that we persist all RIFF chunks
    * Add support for adding GUANO metadata to "new" files
    * Support Anabat files
"""

from __future__ import print_function

import sys, os, os.path
from string import Template

import guano


DRY_RUN = False
MAKE_BACKUPS = True


class GuanoTemplate(Template):
    """
    String template with support for valid GUANO namespaced fields.
    """
    idpattern = r'[_a-z][_a-z0-9| ]*'  # added support for spaces and pipe char


def locate_files(rootdir):
    """Find files with GUANO metadata"""
    if os.path.isdir(rootdir):
        for root, dirnames, filenames in os.walk(rootdir):
            for filename in filenames:
                if filename.endswith('.wav') or filename.endswith('.WAV'):
                    try:
                        yield guano.GuanoFile(os.path.join(root, filename))
                    except ValueError as e:
                        pass
    elif os.path.isfile(rootdir):
        filename = rootdir
        try:
            yield guano.GuanoFile(filename)
        except ValueError as e:
            pass
    else:
        raise RuntimeError(rootdir)


def update(gfile, md, dry_run=False):
    """Update the GUANO metadata in a specified file"""
    print()
    print(gfile.filename)

    for k, v in md.items():
        gfile[k] = GuanoTemplate(v).substitute(gfile)

    print(gfile.to_string())
    if not dry_run:
        gfile.write(make_backup=MAKE_BACKUPS)


def main():
    """Commandline processing script"""
    md = {}      # new metadata values
    inputs = []  # files and folders we're operating on

    for arg in sys.argv[1:]:
        if ':' in arg:
            k, v = (x.strip() for x in arg.split(':', 1))
            md[k] = v
        else:
            inputs.append(arg)

    print(md)

    for input in inputs:
        for gfile in locate_files(input):
            update(gfile, md, dry_run=DRY_RUN)


if __name__ == '__main__':
    main()
