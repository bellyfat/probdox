#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# created: 2016-11-19 18:13:00 by Carsten Knoll

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
import shutil
import errno

# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3


def mkdir_p(path):
    """
    create a path and accept if it alread exists
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            # print(path, 'already exists')
            pass
        else:
            raise


def tolerant_rmtree(target_path):
    """try to delete a tree, and do nothing if it is already absent"""
    try:
        shutil.rmtree(target_path)
    except OSError as exc:  # python >2.5
        if exc.errno == errno.ENOENT:
            pass
        else:
            raise


def write_file(filepath, content):
    path, fname = os.path.split(filepath)

    mkdir_p(path)

    with open(filepath, 'w') as myfile:
        myfile.write(content)


def generate_reference_data(basedir='reference', version='01'):

    filepaths = ['foo/abc.txt',
                 'bar/xyz.dat',
                 'bar/blob/text1.txt'
                ]

    txt1 = "This is sample text\n\nversion %s\n" % version

    for fp in filepaths:
        fp = fp.replace('/', os.path.sep)
        fp = os.path.join(basedir, fp)
        write_file(fp, txt1)
    print('Reference data created.')


if __name__ == '__main__':
    generate_reference_data(sys.argv[1])
