#!/usr/bin/env python
"""
Convert files with SonoBat-format metadata to use GUANO metadata instead.

usage::

    $> sb2guano.py WAVFILE...
"""

from __future__ import print_function

import sys
import os
import os.path
import mmap
import re
import wave
from contextlib import closing
from datetime import datetime
from pprint import pprint

from guano import GuanoFile


# regex for parsing Sonobat metadata
SB_MD_REGEX = re.compile(b'MMMMMMMMM(?P<sb_md>[\w\W]+)MMMMMMMMM')
SB_FREQ_REGEX = re.compile(r'\(#([\d]+)#\)')
SB_TE_REGEX = re.compile(r'<&([\d]*)&>')
SB_DFREQ_REGEX = re.compile(r'\[!([\w]+)!\]')

D500X_ATTRIBUTE_REGEX = re.compile(r'(?P<d500x>D500X V.+S/N=\d+)')
AR125_ATTRIBUTE_REGEX = re.compile(r'(?P<ar125>DEV=.+CMT=<.+>)')

# old SonoBat format e.g. TransectTestRun1-24Mar11-16,27,56-Myoluc.wav
SONOBAT_FILENAME1_REGEX = re.compile(r'(?P<date>[ 0123][0-9][A-Z][a-z][a-z][0-9][0-9]-[012][0-9],[0-6][0-9],[0-6][0-9])(-(?P<species>[A-Za-z]+))?')
SONOBAT_FILENAME1_TIMESTAMP_FMT = '%d%b%y-%H,%M,%S'

# new SonoBat format 4-digit year e.g. TransectTestRun1-20110324_162756-Myoluc.wav
SONOBAT_FILENAME2_REGEX = re.compile(r'(?P<date>\d{8}_\d{6})(-(?P<species>[A-Za-z]+))?')
SONOBAT_FILENAME2_TIMESTAMP_FMT = '%Y%m%d_%H%M%S'

# new new SonoBat format 2-digit year e.g. TransectTestRun1-20110324_162756-Myoluc.wav
SONOBAT_FILENAME3_REGEX = re.compile(r'(?P<date>\d{6}_\d{6})(-(?P<species>[A-Za-z]+))?')
SONOBAT_FILENAME3_TIMESTAMP_FMT = '%y%m%d_%H%M%S'

# AR125 raw
AR125_FILENAME_REGEX = re.compile(r'_(?P<date>D\d{8}T\d{6})m\d{3}(-(?P<species>[A-Za-z]+))?')
AR125_FILENAME_TIMESTAMP_FMT = 'D%Y%m%dT%H%M%S'

SB_FILENAME_FORMATS = [
    (SONOBAT_FILENAME1_REGEX, SONOBAT_FILENAME1_TIMESTAMP_FMT),
    (SONOBAT_FILENAME2_REGEX, SONOBAT_FILENAME2_TIMESTAMP_FMT),
    (SONOBAT_FILENAME3_REGEX, SONOBAT_FILENAME3_TIMESTAMP_FMT),
    (AR125_FILENAME_REGEX,    AR125_FILENAME_TIMESTAMP_FMT)
]


def _decode_text(text):
    """
    SonoBat uses the system locale for encoding text, so we have to guess what it might have been.
    Try Mac_Roman first if we're running on OS X, otherwise default to Windows 1252. Yuck.
    """
    encodings = ['windows-1252', 'latin-1']
    encodings.insert(0 if sys.platform == 'darwin' else 1, 'mac_roman')
    for encoding in encodings:
        try:
            return text.decode(encoding)
        except:
            pass
    raise ValueError('Unable to decode native SonoBat text!')


def _parse_sonobat_metadata(md):
    """Parse Sonobat-format metadata string as a dict"""
    sb_md = dict()
    sb_md['samplerate'] = int(re.search(SB_FREQ_REGEX, md).groups()[0])
    sb_md['te'] = int(re.search(SB_TE_REGEX, md).groups()[0])
    sb_md['dfreq'] = re.search(SB_DFREQ_REGEX, md).groups()[0]
    note = md.split('!]', 1)[1]

    # If this file was created with Sonobat D500X Attributer, parse out D500X metadata
    match = re.search(D500X_ATTRIBUTE_REGEX, note)
    if match and match.group('d500x').count(',') == 8:
        fw, f, pre, len, hp, a, ts, timestamp, sn = match.group('d500x').split(',')
        f, pre, len, hp, a, ts, sn = tuple(s.split('=',1)[1].strip() for s in (f, pre, len, hp, a, ts, sn))
        sb_md['d500x'] = dict(Firmware=fw, F=f, PRE=pre, LEN=len, HP=hp, A=a, TS=ts, Timestamp=timestamp, Serial=sn)

    # Binary Acoustic AR125 stuffs metadata into Sonobat note
    match = re.search(AR125_ATTRIBUTE_REGEX, note)
    if match:
        dev, dc, utc, ltb, cmt = match.group('ar125').split(',', 4)
        dev, dc, utc, ltb, cmt = tuple(s.split('=',1)[1].strip() for s in (dev, dc, utc, ltb, cmt))
        cmt = cmt.strip('<>')
        sb_md['ar125'] = dict(DEV=dev, DC=dc, UTC=utc, LTB=ltb, CMT=cmt)

    sb_md['note'] = note

    return sb_md


def extract_sonobat_metadata(fname):
    """Extract Sonobat-format metadata as a dict"""

    # parse the Sonobat metadata itself from file
    with open(fname, 'rb') as infile:
        with closing(mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)) as mmfile:
            md_match = re.search(SB_MD_REGEX, mmfile)
            if not md_match:
                print('No Sonobat metadata found in file: ' + fname, file=sys.stderr)
                return None
            md = md_match.groups()[0]
            md = _decode_text(md)
            sb_md = _parse_sonobat_metadata(md)

    with closing(wave.open(fname)) as wavfile:
        duration_s = wavfile.getnframes() / float(wavfile.getframerate())
        sb_md['length'] = round(duration_s / sb_md['te'], 2)

    # try to extract info from the filename
    for regex, timestamp_fmt in SB_FILENAME_FORMATS:
        match = regex.search(fname)
        if match:
            sb_md['timestamp'] = datetime.strptime(match.group('date'), timestamp_fmt)
            sb_md['species'] = match.group('species')

    return sb_md


def sonobat2guano(fname):
    """Convert a file with Sonobat metadata to GUANO metadata"""
    print('\n', fname)
    sb_md = extract_sonobat_metadata(fname)
    if not sb_md:
        print('Skipping non-Sonobat file: ' + fname, file=sys.stderr)
        return False
    pprint(sb_md)

    gfile = GuanoFile(fname)
    gfile['GUANO|Version'] = 1.0
    if 'timestamp' in sb_md:
        gfile['Timestamp'] = sb_md['timestamp']
    if sb_md.get('te', 1) != 1:
        gfile['TE'] = sb_md['te']
    gfile['Length'] = sb_md['length']
    gfile['Note'] = sb_md['note'].strip().replace('\r\n', '\\n').replace('\n', '\\n')
    if sb_md.get('species', None):
        gfile['Species Auto ID'] = sb_md['species']

    if 'd500x' in sb_md:
        for k, v in sb_md['d500x'].items():
            gfile['PET', k] = v

    if 'ar125' in sb_md:
        for k, v in sb_md['ar125'].items():
            gfile['BAT', k] = v

    print(gfile.to_string())

    gfile.write()


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
        sonobat2guano(fname)
