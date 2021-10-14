#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from guano import GuanoFile, wavparams, parse_timestamp, tzoffset


class UnicodeTest(unittest.TestCase):

    NOTE = u'¡GUANO is the 💩 !'
    MD = u"""GUANO|Version: 1.0\nNote: %s""" % NOTE

    def setUp(self):
        pass

    def test_from_string(self):
        """Parse a GUANO metadata block containing Unicode data"""
        g = GuanoFile.from_string(self.MD)
        self.assertEqual(self.NOTE, g['Note'])

    def test_file_roundtrip(self):
        """Write a GUANO .WAV file containing Unicode data, re-read it and confirm value is identical"""
        fname = 'test_guano.wav'

        # write a fake .WAV file
        g = GuanoFile.from_string(self.MD)
        g.filename = fname
        g.wav_params = wavparams(1, 2, 500000, 2, 'NONE', None)
        g._wav_data = b'\01\02'  # faking it, don't try this at home!
        g._wav_data_size = 2
        g.write()

        # read it back in
        g2 = GuanoFile(fname)

        self.assertEqual(self.NOTE, g2['Note'])


class GeneralTest(unittest.TestCase):

    MD = r'''GUANO|Version: 1.0
    Timestamp: 2017-04-20T01:23:45-07:00
    Note: This is a \nmultiline text note\nfor testing.
    User|Haiku: five\nseven\nfive
    User|Answer: 42
    MSFT|Transect|Version: 1.0.16
    '''

    def setUp(self):
        GuanoFile.register('User', 'Answer', int)
        self.md = GuanoFile.from_string(self.MD)

    def test_get_namespaces(self):
        """Test that we can extract namespaces"""
        expected = {'GUANO', '', 'User', 'MSFT'}
        namespaces = set(self.md.get_namespaces())
        self.assertSetEqual(expected, namespaces)

    def test_get_types(self):
        """Test multiple ways of requesting a namespaced value"""
        self.assertEqual(42, self.md['User|Answer'])
        self.assertEqual(42, self.md['User', 'Answer'])
        self.assertEqual(42, self.md.get('User|Answer'))

    def test_multiline(self):
        """Ensure multiline string `Note` is parsed as `\n` containing string"""
        self.assertEqual(3, len(self.md['Note'].splitlines()))

    def test_parse_timestamps(self):
        """Verify that we can at least parse all timestamp formats"""
        fmts = [
            '2016-12-10T01:02:03',
            '2016-12-10T01:02:03.123',
            '2016-12-10T01:02:03.123456',

            '2016-12-10T01:02:03Z',
            '2016-12-10T01:02:03.123Z',
            '2016-12-10T01:02:03.123456Z',

            '2016-12-10T01:02:03-07:00',
            '2016-12-10T01:02:03.123-07:00',
            '2016-12-10T01:02:03.123456-07:00',

            '2016-12-10 01:02:03',  # bonus
        ]

        for fmt in fmts:
            try:
                ts = parse_timestamp(fmt)
                ts.isoformat()
            except Exception as e:
                self.fail('Failed parsing: %s  %s' % (fmt, e))

    def test_tzoffset(self):
        """Verify our UTC offset timezone support"""
        fmts = [
            7,
            -7,
            7.0,
            -7.0,

            '07:00',
            '+07:00',
            '-07:00',

            '07',
            '+07',
            '-07',

            '0700',
            '+0700',
            '-0700',
        ]
        for fmt in fmts:
            tz = tzoffset(fmt)
            if abs(tz.utcoffset(None).total_seconds()/60/60) > 8:
                self.fail('Failed parsing UTC offset: %s  %s' % (fmt, tz))
    
    def test_tzoffset_nst(self):
        """Verify fractional tzoffset like Newfoundland NST"""
        offset = tzoffset('-02:30')  # Newfoundland NST
        offset_hours = offset.utcoffset(None).total_seconds() / 60.0 / 60.0
        self.assertEqual(offset_hours, -2.5)

    def test_new_empty(self):
        """Verify that "new" GUANO file metadata is "falsey" but populated metadata is "truthy"."""
        g = GuanoFile('nonexistent_file.wav')
        self.assertFalse(g)
        self.assertFalse('GUANO|Version' in g)

        g['Foo'] = 'bar'
        self.assertTrue(g)
        self.assertTrue('GUANO|Version' in g)

    def test_delete_simple(self):
        """Verify that we can delete fields"""
        g = GuanoFile()
        g['Foo'] = 'xyz'
        self.assertTrue('Foo' in g)

        del g['Foo']
        self.assertFalse('Foo' in g)

        try:
            del g['Foo']
            self.fail('Deleting a deleted key should throw KeyError')
        except KeyError:
            pass

    def test_delete_namespaced(self):
        """Verify that we can delete namespaced fields"""
        g = GuanoFile()
        g['Foo|Bar'] = 'xyz'
        self.assertTrue('Foo|Bar' in g)
        self.assertTrue('Foo' in g.get_namespaces())

        del g['Foo|Bar']
        self.assertFalse('Foo|Bar' in g)
        self.assertFalse('Foo' in g.get_namespaces())

        try:
            del g['Foo|Bar']
            self.fail('Deleting a deleted key should throw KeyError')
        except KeyError:
            pass

        g['Foo|Bar1'] = 'xyz'
        g['Foo|Bar2'] = 'abc'
        del g['Foo|Bar1']
        self.assertFalse('Foo|Bar1' in g)
        self.assertTrue('Foo|Bar2' in g)
        self.assertTrue('Foo' in g.get_namespaces())


class BadDataTest(unittest.TestCase):
    """
    These are hacks that may go against the specification, done in the name of permissive reading.
    John Postel: "Be conservative in what you do, be liberal in what you accept from others."
    """

    def test_sb41_bad_te(self):
        """SonoBat 4.1 "optional" TE value"""
        md = '''GUANO|Version: 1.0
        TE:
        '''
        GuanoFile.from_string(md)

    def test_sb41_bad_key(self):
        """SonoBat 4.1 disembodied colon"""
        md = '''GUANO|Version: 1.0
        :
        '''
        self.assertEqual(1, len(list(GuanoFile.from_string(md).items())))

    def test_sb42_bad_timestamp(self):
        """SonoBat 4.2 blank timestamp"""
        md = '''GUANO|Version: 1.0
        Timestamp:
        '''
        GuanoFile.from_string(md)

    def test_sb42_bad_encoding(self):
        """SonoBat 4.2 doesn't actually encode as UTF-8. At least try not to blow up when reading."""
        # SonoBat *probably* uses mac-roman on OS X and windows-1252 on Windows... in the US at least.
        md = b'GUANO|Version:  1.0\nNote:  Mobile transect with mic 4\xd5 above roof.\n\x00\x00'
        GuanoFile.from_string(md)

    def test_sb42_bad_guano_version(self):
        """Some version of SonoBat 4.2 writes a GUANO|Version of "1.0:" by accident."""
        md = b'GUANO|Version:  1.0:\n1.0:\n'
        GuanoFile.from_string(md)

    def test_empty_values(self):
        """EMTouchPro (and probably others) writes field keys with empty values"""
        md = md = b'GUANO|Version:  1.0\nLoc Elevation:\n'
        GuanoFile.from_string(md)


class StrictParsingTest(unittest.TestCase):
    """
    Test our strict/lenient parsing modes.
    Note that we are always lenient for some types of "bad data", as in :class:BadDataTest above.
    """

    def test_strict_mode(self):
        md = '''GUANO|Version: 1.0
        TE: no
        Loc Position: 10N 567288E 4584472N
        '''
        try:
            GuanoFile.from_string(md, strict=True)
            self.fail('Expected to fail with strict=True')
        except ValueError as e:
            pass
        g = GuanoFile.from_string(md, strict=False)
        self.assertEqual(g.get('TE', None), 'no')
        self.assertEqual(g.get('Loc Position', None), '10N 567288E 4584472N')


if __name__ == '__main__':
    unittest.main()
