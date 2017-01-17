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

try:
    from ipHelp import IPS
except ImportError:
    from IPython import embed as IPS

# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3

BASEDIR = "reference"
CONFIG_PATH = "config.ini"
META_DATA_FNAME = 'metadata.pdx'

# fname for the remote meta data file after download
NEW_REMOTE_META_DATA_FNAME = 'metadata.pdx.remote-new'
OLD_REMOTE_META_DATA_FNAME = 'metadata.pdx.remote-old'
META_DATA_FORMAT_VERSION = 2


# quick and dirty way to store some global variables on module level
class ConfigContainer(object):
    def __init__(self):
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = load_config()

        return self._config


config = ConfigContainer()



class Logger(object):

    def err(self, *args, **kwargs):
        print("Err:", *args, **kwargs)

    def msg(self, *args, **kwargs):
        print("Msg:", *args, **kwargs)

log = Logger()


def mkdir_p(mypath):
    """
    create a path and accept if it alread exists
    """
    try:
        os.makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(mypath):
            # print(path, 'already exists')
            pass
        else:
            raise


def tolerant_rmtree(target_path):
    """try to delete a tree, and do nothing if it is already absent"""
    try:
        shutil.rmtree(target_path)
    except OSError as exc:  # requires python > 2.5
        if exc.errno == errno.ENOENT:
            pass
        else:
            raise


def write_file(filepath, content):
    mypath, fname = os.path.split(filepath)

    mkdir_p(mypath)

    with open(filepath, 'w') as myfile:
        myfile.write(content)


def load_config(mypath=None):
    if mypath is None:
        mypath = CONFIG_PATH
    complete_config = configparser.ConfigParser()
    res = complete_config.read(mypath)
    if len(res) == 0:
        msg = "Config file {} not found".format(mypath)
        raise FileNotFoundError(msg)

    # create a shorthand for the default config
    config = complete_config['DEFAULT']

    return config


def generate_reference_tree(basedir=None, version='01', user=None):
    """
    this function is mainly for testing
    """

    if basedir is None:
        basedir = os.path.join(BASEDIR, config.config['local_data_dir'])

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
                 'bar/dir-empty2'
                 ]

    # dict containing paths that should be absent in each version
    absent_paths = {'01': ['foo/abc3.txt',
                           'bar/blob/text2.txt',
                           'bar/dir-empty2'],
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

    def __init__(self, thepath, normalized=False):
        self._isdir = None
        self._isfile = None
        self.hash_value = None

        # paths

        if normalized:
            assert normalize_paths(thepath) == thepath
            self.nmld_path = thepath
            self.real_lpath = real_lpath_from_nmld_path(thepath)
        else:
            self.nmld_path = normalize_paths(thepath)
            self.real_lpath = thepath

        self.real_rpath = None  # probably obsolete

    def __repr__(self):
        result = "GF({})".format(self.nmld_path)
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
            msg = "Expexted True/False, got unknown Value: %s of type %s." % (value, type(value))
            raise ValueError(msg)

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
            if self.real_lpath is None:
                msg = "Can not find out type of %s without local path" % self
                raise ValueError(msg)

            self._isdir = os.path.isdir(self.real_lpath)
            self._isfile = os.path.isfile(self.real_lpath)

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
            raise ValueError('Unknown file type for %s' % self)
        blocksize = 65536
        hasher = hashlib.sha256()
        # copied from http://pythoncentral.io/hashing-files-with-python/
        with open(self.real_lpath, "rb") as myfile:
            buf = myfile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = myfile.read(blocksize)
        return hasher.hexdigest()

    def to_dict(self, user=None):
        """

        :return:        dictionary like {'a_path': ..., 'type': ..., 'hash': ...}
        """
        assert self.real_lpath is not None
        result = {'hash': self.calc_hash(),
                  'type': self.get_type(),
                  'tstamp': None,
                  'user': user}
        return result


# TODO: refactor to make the scalar case the default
def normalize_paths(pathseq, basedir=None):
    """
    truncate everything before the last segment of basedir

    :param pathseq:     sequence of path strings (or single string)
    :return:
    """

    if isinstance(pathseq, str):
        return_string = True
        pathseq = [pathseq]
    else:
        return_string = False

    if basedir is None:
        # if 0 and config.config is None:
        #     load_config()

        # use the local data dir from the config
        # (assuming it has already been loaded)
        basedir = config.config['local_data_dir']

    result = []

    relevant_segment = os.path.split(basedir)[-1]
    for thepath in pathseq:
        idx = thepath.find(relevant_segment)
        if idx == -1:
            msg = "basedir '%s' was not found in path %s" % (relevant_segment, thepath)
            raise ValueError(msg)

        result.append(thepath[idx:])

    if return_string:
        assert len(result) == 1
        result = result[0]
    return result


def real_lpath_from_nmld_path(thepath, basedir=None):
    """
    Convert a normalized path into a real local path.
    This is the counter operation to normalize_paths.

    :param thepath:
    :param basedir:     a real path of the directory where the
                        normlized path is relative to
    :return:
    """

    if isinstance(thepath, (list, tuple)):
        return [real_lpath_from_nmld_path(p) for p in thepath]

    if basedir is None:
        basedir = config.config['local_data_dir']

    ldd_tail = os.path.split(basedir)[-1]  # only the last part

    # plug in the full path, i.e. all parts which have been
    # removed by normalization
    return thepath.replace(ldd_tail, basedir)


def generate_meta_data(basedir, user=None):

    # this is the top level dict for json
    # it allows to store additional information (not related to any specific file)

    res_dict = {}
    gfiledict = {}  # this will become a dict like {normpath1: {data1}, ...}
    for rootdir, dirs, files in os.walk(basedir):
        # if len(dirs) == len(files) == 0:
        #     # empty directory

        # add the directory itself
        gf = GeneralizedFile(thepath=rootdir)
        gfiledict[gf.nmld_path] = gf.to_dict(user=user)

        for f in files:
            gf = GeneralizedFile(thepath=os.path.join(rootdir, f))
            gfiledict[gf.nmld_path] = gf.to_dict(user=user)

    res_dict['meta_information'] = None
    res_dict['files'] = gfiledict

    return res_dict


def write_json(obj, path):
    with open(path, 'w') as myfile:
        json.dump(obj, myfile, sort_keys=True, indent=4)


def read_json(path):
    with open(path, 'r') as myfile:
        result = json.load(myfile)
    log.msg(path, 'read.')
    return result


def write_meta_data(targetpath, basedir, user):

    data_dict = generate_meta_data(basedir, user)
    write_json(data_dict, targetpath)


if __name__ == '__main__':
    log.msg(sys.argv)
    # generate_reference_data(sys.argv[1], sys.argv[2])

    # !! this should come from the config file (but it is not present on the server)
    local_data_dir = 'data'

    for v in ['01', '02', '03']:
        log.msg('version:', v)
        path = os.path.join(sys.argv[1] + v, local_data_dir)
        generate_reference_tree(path, v)
