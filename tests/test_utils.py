# -*- coding: utf-8 -*-
"""
Unit tests for our extra utility scripts
"""

from __future__ import print_function

import sys
import os
import os.path
import unittest

bin_path = os.path.normpath(os.path.join(os.path.abspath(__file__), '..', '..', 'bin'))
sys.path.insert(0, bin_path)
import wamd2guano
import sb2guano


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


if __name__ == '__main__':
    unittest.main()
