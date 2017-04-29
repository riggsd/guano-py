#!/usr/bin/env python
"""
Convert files from the Elekon BatLogger to use GUANO metadata instead.

usage::

    $> batlogger2guano.py WAVFILE...
"""

from __future__ import print_function

import sys, os, os.path
from datetime import datetime
from xml.etree import ElementTree

from guano import GuanoFile


def get(xml, path, coerce=None, default=None):
    """Extract a value from an ElementTree node"""
    node = xml.find(path)
    if node is None:
        return default
    if coerce is None:
        return node.text
    else:
        return coerce(node.text)


def batlogger2guano(fname):
    """Convert an Elekon BatLogger .WAV with sidecar .XML to GUANO metadata"""
    xmlfname = os.path.splitext(fname)[0] + '.xml'
    if not os.path.exists(xmlfname):
        raise ValueError('Unable to find XML metadata file for %s' % fname)
    g = GuanoFile(fname)
    with open(xmlfname, 'rt') as f:
        xml = ElementTree.parse(f)

    g['Timestamp'] = get(xml, 'DateTime', lambda x: datetime.strptime(x, '%d.%m.%Y %H:%M:%S'))
    g['Firmware Version'] = get(xml, 'Firmware')
    g['Make'] = 'Elekon'
    g['Model'] = 'BatLogger'
    g['Serial'] = get(xml, 'SN')
    g['Samplerate'] = get(xml, 'Samplerate', lambda x: int(x.split()[0]))
    g['Length'] = get(xml, 'Duration', lambda x: float(x.split()[0]))
    g['Original Filename'] = get(xml, 'Filename')
    g['Temperature Ext'] = get(xml, 'Temperature', lambda x: float(x.split()[0]))
    g['Loc Position'] = get(xml, 'GPS/Position', lambda x: tuple(map(float, x.split())))
    g['Loc Elevation'] = get(xml, 'GPS/Altitude', lambda x: float(x.split()[0]))

    g['Elekon|BattVoltage'] = get(xml, 'BattVoltage')
    for node in xml.find('Trigger'):
        g['Elekon|Trigger|%s' % node.tag] = node.text
    for node in xml.find('GPS'):
        g['Elekon|GPS|%s' % node.tag] = node.text

    # for k, v in g.items():
    #     print('%s:\t%s' % (k, v))

    print(g.to_string())
    g.write()
    os.remove(xmlfname)

    return g


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
        print(fname, '...')
        batlogger2guano(fname)
        print()
