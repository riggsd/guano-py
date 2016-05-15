#!/usr/bin/env python
"""
This is the Python reference implementation for reading and writing GUANO metadata.

GUANO is the "Grand Unified Acoustic Notation Ontology", an extensible metadata format
for representing bat acoustics data.
"""


__version__ = '0.0.3'


import os
import sys
import mmap
import wave
import struct
import os.path
import shutil
from datetime import datetime
from contextlib import closing
from tempfile import NamedTemporaryFile


WHITESPACE = ' \t\n\x0b\x0c\r\0'


def parse_timestamp(s):
    """Parse a string in supported subset of ISO 8601 / RFC 3331 format to tz-naive local `datetime`"""
    s = s.replace(' ', 'T', 1)  # support using space rather than 'T' date/time delimiter
    if s[-1] == 'Z':  # time in UTC "zulu"
        # TODO: convert UTC to local? (no guarantee that our "local" was local at recording time)
        return datetime.strptime(s[:-1], '%Y-%m-%dT%H:%M:%S')
    elif len(s) in (22, 25):  # UTC offset provided
        s, offset = s[:19], s[19:]
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    elif len(s) == 26:  # milliseconds included
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


def serialize_timestamp(timestamp):
    if timestamp.microsecond:
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return timestamp.strftime('%Y-%m-%dT%H:%M:%S')


class GuanoFile(object):
    """
    A read-only abstraction of a .WAV file with GUANO metadata.

    A `GuanoFile` object behaves like a normal Python `dict`, where keys can either be well-known
    metadata keys, namespaced keys, or a tuple of (namespace, key).

    Well-known keys will have their values coerced into the correct data type. The parser may be
    configured to coerce new namespaced keys with the `register()` function.

    Example usage:

    gfile = GuanoFile('myfile.wav')

    print gfile['GUANO|Version']
    >>> 1.0

    gfile['SB|Consensus'] = 'Mylu'

    gfile[''] = 'I love GUANO!'

    gfile.write()
    """

    _coersion_rules = {
        'GUANO|Version': float, 'Filter HP': float, 'Length': float, 'Loc Elevation': float,
        'Loc Accuracy': int, 'Samplerate': int, 'TE': int,
        'Loc Position': lambda value: tuple(float(v) for v in value.split()),
        'Timestamp': parse_timestamp,
    }
    _serialization_rules = {
        'Loc Position': lambda value: '%f %f' % value,
        'Timestamp': serialize_timestamp,
    }

    def __init__(self, filename):
        self.filename = filename
        self.wav_data = None
        self.wav_params = None
        self._md = {}  # metadata storage - map of maps:  namespace->key->val

        self._load()

    def _coerce(self, key, value):
        """Coerce a value from its UTF-8 representation to a specific data type"""
        if key in self._coersion_rules:
            return self._coersion_rules[key](value)
        return value  # UTF-8 string

    def _serialize(self, key, value):
        """Serialize a value from its real representation to GUANO UTF-8 representation"""
        serialize = self._serialization_rules.get(key, str)
        return serialize(value)

    def _load(self):
        with open(self.filename, 'rb') as infile:
            with closing(mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)) as mmfile:

                # sanity check validation
                if len(mmfile) < 8:
                    raise ValueError('File too small to contain valid RIFF "WAVE" header (size %d bytes)' % len(mmfile))
                chunk = struct.unpack_from('> 4s', mmfile, 0x08)[0]
                if chunk != 'WAVE':
                    raise ValueError('Expected RIFF chunk "WAVE" at 0x08, but found "%s"' % repr(chunk))

                try:
                    self.wav_params = wave.open(infile).getparams()
                except RuntimeError as e:
                    return ValueError(e)  # Python's chunk.py throws this inappropriate exception

                # iterate through the file until we find our 'guan' subchunk
                metadata_buf = None
                offset = 0x0c
                while offset < len(mmfile)-1:
                    subchunk = struct.unpack_from('> 4s', mmfile, offset)[0]
                    offset += 4
                    size = struct.unpack_from('< I', mmfile, offset)[0]
                    offset += 4
                    if subchunk == 'guan':
                        metadata_buf = mmfile[offset:offset+size]
                    elif subchunk == 'data':
                        self.wav_data = mmfile[offset:offset+size]
                    if size % 2:
                        offset += 1  # align to 16-bit boundary
                    offset += size

                if not self.wav_data:
                    raise ValueError('No DATA sub-chunk found in file')
                if not metadata_buf:
                    #print >> sys.stderr, 'No GUANO metadata found in file: %s' % self.filename
                    return  # this must be a "new" GUANO file

                # split out our metadata keys
                for line in metadata_buf.split('\n'):
                    line = line.strip(WHITESPACE)
                    if not line:
                        continue
                    full_key, val = line.split(':', 1)
                    namespace, key = full_key.split('|', 1) if '|' in full_key else ('', full_key)
                    namespace, key, full_key, val = namespace.strip(), key.strip(), full_key.strip(), val.strip()

                    if namespace not in self._md:
                        self._md[namespace] = {}
                    self._md[namespace][key] = self._coerce(full_key, val)

    @classmethod
    def register(cls, namespace, keys, coerce_function, serialize_function=str):
        """
        Configure the GUANO parser to recognize new namespaced keys.

        :param namespace:  vendor namespace which the keys belong to
        :param keys:  a key or sequence of keys under the specified vendor namespace
        :param coerce_function:  a function for coercing the UTF-8 value to any desired data type
        :param serialize_function:  an optional function for serializing the value to UTF-8 string
        """
        if isinstance(keys, basestring):
            keys = [keys]
        for k in keys:
            full_key = namespace+'|'+k
            cls._coersion_rules[full_key] = coerce_function
            cls._serialization_rules[full_key] = serialize_function

    def __getitem__(self, item):
        if type(item) == tuple:
            namespace, key = item[0], item[1]
        elif '|' in item:
            namespace, key = item.split('|', 1)
        else:
            namespace, key = '', item
        return self._md[namespace][key]

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if type(key) == tuple:
            namespace, key = key[0], key[1]
        elif '|' in key:
            namespace, key = key.split('|', 1)
        else:
            namespace, key = '', key
        if namespace not in self._md:
            self._md[namespace] = {}
        self._md[namespace][key] = value

    def __contains__(self, item):
        if type(item) == tuple:
            namespace, key = item[0], item[1]
        elif '|' in item:
            namespace, key = item.split('|', 1)
        else:
            namespace, key = '', item
        return namespace in self._md and key in self._md[namespace]

    def get_namespaces(self):
        """Get list of all namespaces represented by this metadata"""
        return self._md.keys()

    def items(self, namespace=None):
        """Iterate over (key, value) for entire metadata or for specified namespace of fields"""
        if namespace is not None:
            for k, v in self._md[namespace].items():
                yield k, v
        else:
            for namespace, data in self._md.items():
                for k, v in data.items():
                    k = '%s|%s' % (namespace, k) if namespace else k
                    yield k, v

    def items_namespaced(self):
        """Iterate over (namespace, key, value) for entire metadata"""
        for namespace, data in self._md.items():
            for k, v in data.items():
                yield namespace, k, v

    def well_known_items(self):
        """Iterate over (key, value) for all the well-known (defined) fields"""
        return self.items('')

    def _as_string(self):
        lines = []
        for namespace, data in self._md.items():
            for k, v in data.items():
                k = u'%s|%s' % (namespace, k) if namespace else k
                v = self._serialize(k, v)
                lines.append(u'%s: %s' % (k, v))
        return u'\n'.join(lines)

    def write(self, make_backup=True):
        """Write the GUANO file to disk"""
        # prepare our metadata for a byte-wise representation
        md_bytes = bytearray(self._as_string(), 'utf-8')
        if len(md_bytes) % 2:
            md_bytes.append(ord('\n'))  # pad for alignment on even word boundary

        # create tempfile and write our vanilla .WAV ('data' sub-chunk only)
        tempfile = NamedTemporaryFile(mode='w+b', prefix='guano_temp-', suffix='.wav', delete=False)
        shutil.copystat(self.filename, tempfile.name)
        with closing(wave.Wave_write(tempfile)) as wavfile:
            wavfile.setparams(self.wav_params)
            wavfile.writeframes(self.wav_data)

        # add the 'guan' sub-chunk after the 'data' sub-chunk
        tempfile.seek(tempfile.tell())
        tempfile.write(struct.pack('<4sL', 'guan', len(md_bytes)))
        tempfile.write(md_bytes)

        # fix the RIFF file length
        total_size = tempfile.tell()
        tempfile.seek(0x04)
        tempfile.write(struct.pack('<L', total_size - 8))
        tempfile.close()

        # verify it
        GuanoFile(tempfile.name)

        # finally overwrite the original with our new version
        if make_backup:
            backup_dir = os.path.join(os.path.dirname(self.filename), 'GUANO_BACKUP')
            backup_file = os.path.join(backup_dir, os.path.basename(self.filename))
            if not os.path.isdir(backup_dir):
                print >> sys.stderr, 'Creating backup dir: ' + backup_dir
                os.mkdir(backup_dir)
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(self.filename, backup_file)
        os.rename(tempfile.name, self.filename)


if __name__ == '__main__':
    from pprint import pprint

    if len(sys.argv) < 2:
        print >> sys.stderr, 'usage: guano.py FILENAME...'
        sys.exit(2)

    # the following is an example of how to register a few namespaced keys with data type coercion
    GuanoFile.register('SB', ['DiscrProb', 'Version'], float)
    GuanoFile.register('Anabat', ['Humidity', 'Temperature'], float)
    GuanoFile.register('Anabat', 'Start', parse_timestamp, serialize_timestamp)

    for fname in sys.argv[1:]:
        print '\n' + fname
        guanofile = GuanoFile(fname)
        pprint(guanofile._md)

        for k, v in guanofile.items():
            print '%s:  %s' % (k, v)

        if 'GUANO|Version' in guanofile:
            print '\nValid GUANO file, version %s' % guanofile['GUANO|Version']
