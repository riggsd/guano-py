#!/usr/bin/env python
"""
This is the Python reference implementation for reading and writing GUANO metadata.

GUANO is the "Grand Unified Acoustic Notation Ontology", an extensible metadata format
for representing bat acoustics data.
"""


__version__ = '0.0.5'


import os
import sys
import mmap
import wave
import struct
import os.path
import shutil
from datetime import datetime, tzinfo, timedelta
from contextlib import closing
from tempfile import NamedTemporaryFile
from collections import OrderedDict, namedtuple
from base64 import standard_b64encode as base64encode
from base64 import standard_b64decode as base64decode


__all__ = 'GuanoFile',


WHITESPACE = ' \t\n\x0b\x0c\r\0'

wavparams = namedtuple('wavparams', 'nchannels, sampwidth, framerate, nframes, comptype, compname')


_ZERO = timedelta(0)

class tzutc(tzinfo):
    """UTC timezone"""

    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return _ZERO

    def __repr__(self):
        return 'UTC'

utc = tzutc()

class tzoffset(tzinfo):
    """
    Fixed-offset concrete timezone implementation.
    `offset` should be numeric hours or ISO format string like '-07:00'.
    """

    def __init__(self, offset=None):
        if isinstance(offset, basestring):
            # offset as ISO string '-07:00' or '-07' format
            vals = offset.split(':')
            offset = int(vals[0]) if len(vals) == 1 else int(vals[0]) + int(vals[1])/60.0
        self._offset_hours = offset
        self._offset = timedelta(hours=offset)

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return _ZERO

    def tzname(self, dt):
        return 'UTC'+str(self._offset_hours)

    def __repr__(self):
        return self.tzname(None)


def parse_timestamp(s):
    """Parse a string in supported subset of ISO 8601 / RFC 3331 format to tz-naive local `datetime`"""
    # Python's standard library does an awful job of parsing ISO timestamps, so we do it manually
    timestamp, tz = None, None

    s = s.replace(' ', 'T', 1)  # support using space rather than 'T' as date/time delimiter

    if s[-1] == 'Z':  # UTC "zulu" time
        tz = utc
        s = s[:-1]
    elif '+' in s or s.count('-') == 3:  # UTC offset provided
        i = s.index('+') if '+' in s else s.rfind('-')
        s, offset = s[:i], s[i:]
        tz = tzoffset(offset)

    if len(s) > 22:  # milliseconds included
        timestamp = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        timestamp = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')

    return timestamp.replace(tzinfo=tz) if tz else timestamp


class GuanoFile(object):
    """
    An abstraction of a .WAV file with GUANO metadata.

    A `GuanoFile` object behaves like a normal Python `dict`, where keys can either be well-known
    metadata keys, namespaced keys, or a tuple of (namespace, key).

    Well-known keys will have their values coerced into the correct data type. The parser may be
    configured to coerce new namespaced keys with the `register()` function.

    Example usage:

        gfile = GuanoFile('myfile.wav')
        print gfile['GUANO|Version']
        >>> 1.0
        gfile['Species Manual ID'] = 'Mylu'
        gfile['Comment'] = 'I love GUANO!'
        gfile.write()

    While reading, writing, and editing .WAV files is the target usage, this class may also be
    used completely separate from the .WAV file format. GUANO metadata can be written into an
    Anabat-format file or to a sidecar file, for example, by populating a `GuanoFile` object and
    then using the `serialize()` method to produce correctly formatted UTF-8 encoded metadata.
    """

    _coersion_rules = {
        'GUANO|Version': float, 'Filter HP': float, 'Length': float, 'Loc Elevation': float,
        'Loc Accuracy': int, 'Samplerate': int, 'TE': int,
        'Loc Position': lambda value: tuple(float(v) for v in value.split()),
        'Timestamp': parse_timestamp,
    }
    _serialization_rules = {
        'Loc Position': lambda value: '%f %f' % value,
        'Timestamp': lambda value: value.isoformat(),
        'Length': lambda value: '%.2f' % value
    }

    def __init__(self, filename=None):
        self.filename = filename
        self.wav_data = None
        self.wav_params = None
        self._md = OrderedDict()  # metadata storage - map of maps:  namespace->key->val

        if filename is not None and os.path.isfile(filename):
            self._load()
        else:
            self._initialize_new_metadata()

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
        """Load the contents of our underlying .WAV file"""
        with open(self.filename, 'rb') as infile:
            with closing(mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)) as mmfile:

                # sanity check validation
                if len(mmfile) < 8:
                    raise ValueError('File too small to contain valid RIFF "WAVE" header (size %d bytes)' % len(mmfile))
                chunk = struct.unpack_from('> 4s', mmfile, 0x08)[0]
                if chunk != 'WAVE':
                    raise ValueError('Expected RIFF chunk "WAVE" at 0x08, but found "%s"' % repr(chunk))

                try:
                    self.wav_params = wavparams(*wave.open(infile).getparams())
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
                    raise ValueError('No DATA sub-chunk found in .WAV file')
                if not metadata_buf:
                    # no 'guan' chunk, so treat this as brand new metadata
                    self._initialize_new_metadata()
                    return

                self._parse(metadata_buf)

    def _initialize_new_metadata(self):
        self['GUANO|Version'] = '1.0'

    def _parse(self, metadata_str):
        """Parse metadata and populate our internal mappings"""
        for line in metadata_str.split('\n'):
            line = line.strip(WHITESPACE)
            if not line:
                continue
            full_key, val = line.split(':', 1)
            namespace, key = full_key.split('|', 1) if '|' in full_key else ('', full_key)
            namespace, key, full_key, val = namespace.strip(), key.strip(), full_key.strip(), val.strip()

            if namespace not in self._md:
                self._md[namespace] = OrderedDict()
            self._md[namespace][key] = self._coerce(full_key, val)
        return self

    @classmethod
    def from_string(cls, metadata_str):
        """
        Create a `GuanoFile` instance from a GUANO metadata string

        :param metadata_str:  a string (or string-like buffer) of GUANO metadata
        :rtype:  GuanoFile
        """
        return GuanoFile()._parse(metadata_str)

    @classmethod
    def register(cls, namespace, keys, coerce_function, serialize_function=str):
        """
        Configure the GUANO parser to recognize new namespaced keys.

        :param namespace:  vendor namespace which the keys belong to
        :param keys:  a key or sequence of keys under the specified vendor namespace
        :param coerce_function:  a function for coercing the UTF-8 value to any desired data type
        :type coerce_function:  callable
        :param serialize_function:  an optional function for serializing the value to UTF-8 string
        :type serialize_function:  callable
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
        """Represent the GUANO metadata as a UTF-8 String"""
        lines = []
        for namespace, data in self._md.items():
            for k, v in data.items():
                k = u'%s|%s' % (namespace, k) if namespace else k
                v = self._serialize(k, v)
                lines.append(u'%s: %s' % (k, v))
        return u'\n'.join(lines)

    def serialize(self, pad='\n'):
        """Serialize the GUANO metadata as UTF-8 encoded bytes"""
        md_bytes = bytearray(self._as_string(), 'utf-8')
        if pad is not None and len(md_bytes) % 2:
            # pad for alignment on even word boundary
            md_bytes.append(ord(pad))
        return md_bytes

    def write(self, make_backup=True):
        """
        Write the GUANO .WAV file to disk.

        :raises ValueError:  if this `GuanoFile` doesn't represent a valid .WAV by having
                             appropriate values for `self.wav_params` (see `wavfile.setparams()`)
                             and `self.wav_data` (see `wavfile.writeframes()`)
        """
        # FIXME: optionally write other unknown subchunks for redundant metadata formats

        if not self.filename:
            raise ValueError('Cannot write .WAV file without a self.filename!')
        if not self.wav_params:
            raise ValueError('Cannot write .WAV file without appropriate self.wav_params (see `wavfile.setparams()`)')
        if not self.wav_params:
            raise ValueError('Cannot write .WAV file without appropriate self.wav_data (see `wavfile.writeframes()`)')

        # prepare our metadata for a byte-wise representation
        md_bytes = self.serialize()

        # create tempfile and write our vanilla .WAV ('data' sub-chunk only)
        tempfile = NamedTemporaryFile(mode='w+b', prefix='guano_temp-', suffix='.wav', delete=False)
        if os.path.isfile(self.filename):
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

        # verify it by re-parsing the new version
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
    GuanoFile.register('SB', ['DiscrProb', 'MeanTBC'], float)
    GuanoFile.register('Anabat', ['Humidity', 'Temperature'], float)
    GuanoFile.register('Anabat', 'Start', parse_timestamp, lambda x: x.isoformat())

    for fname in sys.argv[1:]:
        print '\n' + fname
        guanofile = GuanoFile(fname)
        pprint(guanofile._md)

        for k, v in guanofile.items():
            print '%s:  %s' % (k, v)

        if 'GUANO|Version' in guanofile:
            print '\nValid GUANO file, version %s' % guanofile['GUANO|Version']
