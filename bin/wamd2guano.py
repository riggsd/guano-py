#!/usr/bin/python
"""
Convert Wildlife Acoustics WAMD metadata files to use GUANO metadata instead.

usage::

    $> wamd2guano.py WAVFILE...
"""

from __future__ import print_function

import os
import os.path
import sys
import chunk
import struct
from datetime import datetime
from pprint import pprint

from guano import GuanoFile, tzoffset


# binary WAMD field identifiers
WAMD_IDS = {
    0x00: 'version',
    0x01: 'model',
    0x02: 'serial',
    0x03: 'firmware',
    0x04: 'prefix',
    0x05: 'timestamp',
    0x06: 'gpsfirst',
    0x07: 'gpstrack',
    0x08: 'software',
    0x09: 'license',
    0x0A: 'notes',
    0x0B: 'auto_id',
    0x0C: 'manual_id',
    0x0D: 'voicenotes',
    0x0E: 'auto_id_stats',
    0x0F: 'time_expansion',
    0x10: 'program',
    0x11: 'runstate',
    0x12: 'microphone',
    0x13: 'sensitivity',
}

# fields that we exclude from our in-memory representation
WAMD_DROP_IDS = (
    0x0D,    # voice note embedded .WAV
    0x10,    # program binary
    0x11,    # runstate giant binary blob
    0xFFFF,  # used for 16-bit alignment
)

# rules to coerce values from binary string to native types (default is `str`)
WAMD_COERCE = {
    'version': lambda x: struct.unpack('<H', x)[0],
    'timestamp': lambda x: _parse_wamd_timestamp(x),
    'gpsfirst': lambda x: _parse_wamd_gps(x),
    'time_expansion': lambda x: struct.unpack('<H', x)[0],
}


def _parse_text(value):
    """Default coercion function which assumes text is UTF-8 encoded"""
    return value.decode('utf-8')


def _parse_wamd_timestamp(timestamp):
    """WAMD timestamps are one of these known formats:
    2014-04-02 22:59:14-05:00
    2014-04-02 22:59:14.000
    2014-04-02 22:59:14
    Produces a `datetime.datetime`.
    """
    if isinstance(timestamp, bytes):
        timestamp = timestamp.decode('utf-8')
    if len(timestamp) == 25:
        dt, offset = timestamp[:-6], timestamp[19:]
        tz = tzoffset(offset)
        return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz)
    elif len(timestamp) == 23:
        return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    elif len(timestamp) == 19:
        return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    else:
        return None


def _parse_wamd_gps(gpsfirst):
    """WAMD "GPS First" waypoints are in one of these two formats:
    SM3, SM4, (the correct format):
        WGS..., LAT, N|S, LON, E|W [, alt...]
    EMTouch:
        WGS..., [-]LAT, [-]LON[,alt...]
    Produces (lat, lon, altitude) float tuple.
    """
    if not gpsfirst:
        return None
    if isinstance(gpsfirst, bytes):
        gpsfirst = gpsfirst.decode('utf-8')
    vals = tuple(val.strip() for val in gpsfirst.split(','))
    datum, vals = vals[0], vals[1:]
    if vals[1] in ('N', 'S'):
        # Standard format
        lat, lon = float(vals[0]), float(vals[2])
        if vals[1] == 'S':
            lat *= -1
        if vals[3] == 'W':
            lon *= -1
        alt = int(round(float(vals[4]))) if len(vals) > 4 else None
    else:
        # EMTouch format
        lat, lon = float(vals[0]), float(vals[1])
        alt = int(round(float(vals[2]))) if len(vals) > 2 else None
    return lat, lon, alt


def wamd(fname):
    """Extract WAMD metadata from a .WAV file as a dict"""
    with open(fname, 'rb') as f:
        ch = chunk.Chunk(f, bigendian=False)
        if ch.getname() != b'RIFF':
            raise Exception('%s is not a RIFF file!' % fname)
        if ch.read(4) != b'WAVE':
            raise Exception('%s is not a WAVE file!' % fname)

        wamd_chunk = None
        while True:
            try:
                subch = chunk.Chunk(ch, bigendian=False)
            except EOFError:
                break
            if subch.getname() == b'wamd':
                wamd_chunk = subch
                break
            else:
                subch.skip()
        if not wamd_chunk:
            raise Exception('"wamd" WAV chunk not found in file %s' % fname)

        metadata = {}
        offset = 0
        size = wamd_chunk.getsize()
        buf = wamd_chunk.read(size)
        while offset < size:
            id = struct.unpack_from('< H', buf, offset)[0]
            len = struct.unpack_from('< I', buf, offset+2)[0]
            val = struct.unpack_from('< %ds' % len, buf, offset+6)[0]
            if id not in WAMD_DROP_IDS:
                name = WAMD_IDS.get(id, id)
                val = WAMD_COERCE.get(name, _parse_text)(val)
                metadata[name] = val
            offset += 6 + len
        return metadata


def wamd2guano(fname):
    """Convert a Wildlife Acoustics WAMD metadata file to GUANO metadata format"""
    wamd_md = wamd(fname)
    pprint(wamd_md)

    gfile = GuanoFile(fname)
    gfile['GUANO|Version'] = 1.0

    gfile['Timestamp'] = wamd_md.pop('timestamp')
    gfile['Note'] = wamd_md.pop('notes', '')

    gfile['Make'] = 'Wildlife Acoustics'
    gfile['Model'] = wamd_md.pop('model', '')
    gfile['Firmware Version'] = wamd_md.pop('firmware', '')

    gfile['Species Auto ID'] = wamd_md.pop('auto_id', '')
    gfile['Species Manual ID'] = wamd_md.pop('manual_id', '')

    gfile['TE'] = wamd_md.pop('time_expansion', 1)
    gfile['Samplerate'] = gfile.wav_params.framerate * gfile['TE']
    gfile['Length'] = gfile.wav_params.nframes / float(gfile.wav_params.framerate) * gfile['TE']

    if 'gpsfirst' in wamd_md:
        lat, lon, alt = wamd_md.pop('gpsfirst')
        gfile['Loc Position'] = lat, lon
        gfile['Loc Elevation'] = alt

    for k, v in wamd_md.items():
        gfile['WA', k] = v

    print(gfile.to_string())

    gfile.write()


def main():
    from glob import glob

    if len(sys.argv) < 2:
        print('usage: %s FILE...' % os.path.basename(sys.argv[0]), file=sys.stderr)
        sys.exit(2)

    if os.name == 'nt' and '*' in sys.argv[1]:
        fnames = glob(sys.argv[1])
    else:
        fnames = sys.argv[1:]

    for fname in fnames:
        print(fname)
        try:
            wamd2guano(fname)
        except Exception as e:
            import traceback
            traceback.print_exc()
            #print(e, file=sys.stderr)
        print()


if __name__ == '__main__':
    main()
