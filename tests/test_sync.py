#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# created: 2016-11-19 17:18:00 by Carsten Knoll

"""
This file is part of probdox.

probdox is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os
import unittest
from probdox.util import fsutils

from IPython import embed as IPS


# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3


class TestSync1(unittest.TestCase):

    def setUp(self):
        fsutils.generate_reference_tree()

    def tearDown(self):
        fsutils.tolerant_rmtree('reference')

    def test_pull(self):
        pass


class TestInternals(unittest.TestCase):

    def setUp(self):
        fsutils.generate_reference_tree()

    def tearDown(self):
        fsutils.tolerant_rmtree('reference')

    def test_normalized_paths(self):

        ldd_tail = os.path.split(fsutils.config.local_data_dir)[-1]
        my_nmld_path = os.path.join(ldd_tail, 'foo/bar')
        real_lpath = fsutils.real_lpath_from_nmld_path(my_nmld_path)
        res = fsutils.normalize_paths(real_lpath)
        self.assertEqual(res, my_nmld_path)

    # TODO: Test with different working directories
    # TODO: Test IPS residues


if __name__ == '__main__':
    unittest.main()
