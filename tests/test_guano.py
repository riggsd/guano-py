#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from guano import GuanoFile, wavparams


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
        g.wav_data = b'\0\0'
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
        GuanoFile.register('', 'Note', lambda x: x.replace('\\n', '\n'))
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


class BadDataTest(unittest.TestCase):
    """
    These are hacks that may go against the specification, done in the name of permissive reading.
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


if __name__ == '__main__':
    unittest.main()
