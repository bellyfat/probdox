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
        print('Reference data removed.')

    def test_pull(self):
        pass


if __name__ == '__main__':
    unittest.main()
