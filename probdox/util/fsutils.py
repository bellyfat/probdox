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
import hashlib
import json
import configparser
from IPython import embed as IPS

# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3

BASEDIR = "reference"
CONFIG_PATH = "config.ini"
META_DATA_FNAME = 'metadata.pdx'

class Logger(object):

    def err(self, *args, **kwargs):
        print("Err:", *args, **kwargs)

    def msg(self, *args, **kwargs):
        print("Msg:", *args, **kwargs)

log = Logger()


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


def load_config(path=None):
    if path is None:
        path = CONFIG_PATH
    complete_config = configparser.ConfigParser()
    complete_config.read(path)

    # create a shorthand for the default config
    config = complete_config['DEFAULT']

    return config


def generate_reference_data(basedir=BASEDIR, version='01', user=None):

    # these data structures contain all possible reference files
    # version differences are applied via diffs
    filepaths = ['abc.txt',
                 'foo/abc.txt',
                 'foo/abc3.txt',
                 'bar/xyz.dat',
                 'bar/blob/text1.txt',
                 'bar/blob/text2.txt'
                ]
    emptydirs = ['dir-empty1',
                 'bar/dir-empty2,'
                 ]

    # dict containing paths that should be absent in each version
    absent_paths = {'01': ['foo/abc3.txt',
                           'bar/blob/text2.txt',
                           'dir-empty1'],
                    '02': ['foo/abc3.txt'],
                    '03': ['bar/blob/text2.txt']}

    contents = {'01': "This is sample text.",
                '02': "This is sample text.",
                '03': "This is sample text\n\nversion 3.",
                }

    for ap in absent_paths[version]:
        if ap in filepaths:
            filepaths.remove(ap)
        elif ap in emptydirs:
            emptydirs.remove(ap)
        else:
            msg = "Could not remove %s from list because it was not found." % ap
            IPS()
            raise ValueError(msg)

    txt = contents[version]

    # clear legacy residues
    tolerant_rmtree(basedir)

    for fp in filepaths:
        fp = fp.replace('/', os.path.sep)
        fp = os.path.join(basedir, fp)
        write_file(fp, txt)

    for d in emptydirs:
        d = d.replace('/', os.path.sep)
        d = os.path.join(basedir, d)
        mkdir_p(d)

    print('Reference data created.')

    targetpath = os.path.join(basedir, META_DATA_FNAME)
    write_meta_data(targetpath, basedir, user)


class GeneralizedFile(object):
    """
    Hold information about a generalized file (file or directory)
    """

    def __init__(self, rpath, lpath=None):
        self._isdir = None
        self._isfile = None
        self.hash_value = None

        self.rpath = rpath
        self.lpath = lpath

        log.msg(self, "created")

    def __repr__(self):
        result = "GF(%s | %s)" % (self.rpath, self.lpath)
        return result

    def isdir(self, value=None):
        if value is None:
            return self._isdir
        elif value in (True, False):
            assert self._isdir is None
            self._isdir = value
            assert self._isfile is None
            self._isfile = not value
        else:
            raise ValueError("Expexted True/False, got unknown Value: %s of type %s." % (value, type(value)))

    def isfile(self, value=None):
        if value is None:
            return self._isfile
        else:
            if value in (True, False):
                self.isdir(not value)
            else:
                # use error handling in the other method
                self.isdir(value)

    def get_type(self):
        if None in (self._isdir, self._isfile):
            # type not yet specified

            # try to find out in local context
            if self.lpath is None:
                msg = "Can not find out type of %s without local path" % self
                raise ValueError(msg)

            self._isdir = os.path.isdir(self.lpath)
            self._isfile = os.path.isfile(self.lpath)

        if self._isdir:
            return "dir"
        elif self._isfile:
            return 'file'
        else:
            return 'unspecified'

    def calc_hash(self):
        self.get_type()
        if self.isdir():
            return None

        if not self.isfile():
            IPS()
            assert False
        blocksize = 65536
        hasher = hashlib.sha256()
        # copied from http://pythoncentral.io/hashing-files-with-python/
        with open(self.lpath, "rb") as myfile:
            buf = myfile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = myfile.read(blocksize)
        return hasher.hexdigest()

    def to_dict(self, user=None):
        """

        :return:        dictionary like {'a_path': ..., 'type': ..., 'hash': ...}
        """
        assert self.lpath is not None
        result = {'hash': self.calc_hash(),
                  'type': self.get_type(),
                  'tstamp': None,
                  'user': user}
        return result


def generate_meta_data(basedir, user=None):

    # this is the top level dict for json
    # it allows to store additional information (not related to any specific file)

    res_dict = {}
    filedict = {}  # this will become a dict like {fname1: {data1}, ...}
    for root, dirs, files in os.walk(basedir):
        # if len(dirs) == len(files) == 0:
        #     # empty directory

        gf = GeneralizedFile(rpath=None, lpath=root)
        filedict[gf.lpath] = gf.to_dict(user=user)

        for f in files:
            path = os.path.join(root, f)
            gf = GeneralizedFile(rpath=None, lpath=path)
            filedict[gf.lpath] = gf.to_dict(user=user)

    res_dict['meta_information'] = None
    res_dict['files'] = filedict

    return res_dict


def write_meta_data(targetpath, basedir, user):

    data_dict = generate_meta_data(basedir, user)

    with open(targetpath, 'w') as myfile:
        json.dump(data_dict, myfile, indent=4)


if __name__ == '__main__':
    log.msg(sys.argv)
    # generate_reference_data(sys.argv[1], sys.argv[2])

    for v in ['01', '02', '03']:
        log.msg('version:', v)
        generate_reference_data(sys.argv[1] + v, v)
