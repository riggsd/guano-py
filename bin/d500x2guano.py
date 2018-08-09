#!/usr/bin/env python
"""
Convert files with raw D500X metadata to use GUANO metadata instead.

usage::

    $> d500x2guano.py WAVFILE...
"""

from __future__ import print_function

import sys
import os
import os.path
import mmap
import wave
import stat
import struct
from contextlib import closing
from datetime import datetime
from pprint import pprint

from guano import GuanoFile


D500X_DATA_SKIP_BYTES = 0x3D4


def dms2decimal(dms_str):
    """Convert D500X Degrees-Minuts-Seconds to Decimal Degrees"""
    d, m, s, direction = dms_str.split()
    sign = -1 if direction in ('S', 'W') else 1
    return sign * (int(d) + float(m) / 60 + float(s) / 3600)


def unlock(fname):
    """Enable filesystem modification of a locked file"""
    if os.name == 'nt':
        os.chmod(fname, stat.S_IWRITE)
    elif os.name == 'posix' and hasattr(os, 'chflags'):
        os.chflags(fname, os.stat(fname).st_flags & ~stat.UF_IMMUTABLE)


def extract_d500x_metadata(fname):
    """Extract raw D500X metadata as a dict, or None if file has none"""
    md = {}
    with open(fname, 'rb') as infile:
        with closing(mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)) as mmfile:
            if mmfile[0xF0:0xF0+5] != b'D500X':
                print('No D500X metadata found in file: ' + fname, file=sys.stderr)
                return None

            md['Samplerate'] = struct.unpack_from('< i', mmfile, 0x18)[0]
            md['File Name'] = mmfile[0xD0:0xD0+10].decode('latin-1')
            md['File Time'] = mmfile[0xE0:0xE0+15].decode('latin-1')
            md['FW Version'] = mmfile[0xF0:0xF0+32].strip(b'\0 ').decode('latin-1')
            profile_settings_1 = mmfile[0x120:0x120+20].strip(b'\0 ').decode('latin-1')
            profile_settings_2 = mmfile[0x138:0x138+16].strip(b'\0 ').decode('latin-1')
            for tok in (profile_settings_1 + ' ' + profile_settings_2).split():
                k, v = tok.split('=', 1)
                md['Profile ' + k] = v
            # TODO:  0x150 - 0x157 ?
            md['Profile Name'] = mmfile[0x158:0x158+8].strip(b'\0\xFF ').decode('latin-1')

            # block from 0x200 - 0x400 is a big '\r\n' delimited string. 2.0+ firmware only
            extra_md_block = mmfile[0x200:0x400].strip().decode('latin-1')
            if extra_md_block:
                for line in extra_md_block.splitlines():
                    if not line.strip('\0 '):
                        continue
                    k, v = line.split(':', 1)
                    md[k] = v.strip('\0 ')

            md['File Time'] = datetime.strptime(md['File Time'], '%y%m%d %H:%M:%S')

    with closing(wave.open(fname)) as wavfile:
        frame_count = wavfile.getnframes() - (D500X_DATA_SKIP_BYTES / wavfile.getsampwidth())
        duration_s = frame_count / float(wavfile.getframerate())
        md['Length'] = round(duration_s, 2)

    return md


def d500x2guano(fname):
    """Convert a file with raw D500X metadata to use GUANO metadata instead"""
    print('\n', fname)
    md = extract_d500x_metadata(fname)
    if not md:
        print('Skipping non-D500X file: ' + fname, file=sys.stderr)
        return False
    #pprint(md)

    gfile = GuanoFile(fname)
    gfile['GUANO|Version'] = 1.0

    gfile['Make'] = 'Pettersson'
    gfile['Model'] = 'D500X'
    gfile['Timestamp'] = md.pop('File Time')
    gfile['Original Filename'] = md.pop('File Name')
    gfile['Samplerate'] = md.pop('Samplerate')
    gfile['Length'] = md.pop('Length')

    if md.get('Profile HP', None) == 'Y':
        gfile['Filter HP'] = 20

    lat, lon = md.pop('LAT', None), md.pop('LON', None)
    if lat and lon:
        gfile['Loc Position'] = dms2decimal(lat), dms2decimal(lon)

    for k, v in md.items():
        gfile['PET', k] = v

    print(gfile.to_string())

    # throw out the Pettersson metadata bytes from 'data' chunk
    gfile.wav_data = gfile.wav_data[D500X_DATA_SKIP_BYTES:]

    unlock(fname)  # D500X "locks" files as unwriteable, we must unlock before we can modify
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
        d500x2guano(fname)
