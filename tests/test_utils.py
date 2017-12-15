# -*- coding: utf-8 -*-
"""
Unit tests for our extra utility scripts
"""

from __future__ import print_function

import sys
import os
import os.path
import unittest
from itertools import chain

from guano import GuanoFile

bin_path = os.path.normpath(os.path.join(os.path.abspath(__file__), '..', '..', 'bin'))
sys.path.insert(0, bin_path)
import sb2guano
import wamd2guano
from guano_edit import GuanoTemplate



class WamdTest(unittest.TestCase):

    def test_timestamps(self):
        for val in [
            b'2014-04-02 22:59:14-05:00',
            b'2014-04-02 22:59:14.000',
            b'2014-04-02 22:59:14',
        ]:
            ts = wamd2guano._parse_wamd_timestamp(val)

    def test_gps(self):
        for val in [
            b'WGS84, 41.713889, N, 121.508333, W',
            b'WGS84, 41.713889, N, 121.508333, W , 4200',
            b'WGS84, 41.713889, -21.508333',
            b'WGS84, 41.713889, -21.508333, 4200',
        ]:
            lat, lon, alt = wamd2guano._parse_wamd_gps(val)


class SonoBatTest(unittest.TestCase):

    def test_ar125(self):
        md = 'MMMMMMMMM(#25000#)<&10&>[!250!]DEV=AR125RevA,DC=Off,UTC=2011:04:17::04:25:49.089,LTB=420,CMT=<BAT FR125 Field Recording Unit>MMMMMMMMM'
        md = sb2guano._parse_sonobat_metadata(md)
        #print(md)
        # TODO: parse the AR125 specific fields out separately


class GuanoEditTest(unittest.TestCase):

    def setUp(self):
        self.g = g = GuanoFile()
        g['A'] = 'A value'
        g['Foo Bar'] = 'Foo Bar value'
        g['NS|C'] = 'C value'
        g['NS|Foo Bar'] = 'Namespaced Foo Bar value'

    def test_template_1(self):
        s = GuanoTemplate('${A}').substitute(self.g)
        self.assertEqual(s, 'A value')

    def test_template_2(self):
        s = GuanoTemplate('${Foo Bar}').substitute(self.g)
        self.assertEqual(s, 'Foo Bar value')

    def test_template_3(self):
        s = GuanoTemplate('${NS|C}').substitute(self.g)
        self.assertEqual(s, 'C value')

    def test_template_4(self):
        s = GuanoTemplate('${NS|Foo Bar}').substitute(self.g)
        self.assertEqual(s, 'Namespaced Foo Bar value')

    def test_template_fail(self):
        try:
            GuanoTemplate('${DOES NOT EXIST}').substitute(self.g)
            self.fail('Expected failure with KeyError for nonexistent template substitution key')
        except KeyError:
            pass

    def test_well_known(self):
        # pretend this is an exhaustive list of well-known fields!
        # FIXME: because these are class attributes, we "accumulate" fields within the unit testing process
        keys = set(chain(GuanoFile._coersion_rules.keys(), GuanoFile._serialization_rules.keys()))
        for key in keys:
            self.g[key] = key
            s = GuanoTemplate('${'+key+'}').substitute(self.g)
            self.assertEqual(s, key)


if __name__ == '__main__':
    unittest.main()
