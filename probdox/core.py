#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# created: 2016-11-19 14:43:45 by Carsten Knoll

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
import argparse
import paramiko
import stat
import probdox.util.fsutils as fsu
from probdox.util.fsutils import log, GeneralizedFile

from ipHelp import IPS

# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3


class Manager(object):

    def __init__(self):
        self.nrmd_path = None
        self.ormd_path = None
        self.lmd_path = None
        self.sftp = None
        self.config = None
        self.host = None
        self.port = None
        self.username = None
        self.local_aux_dir = None
        self.local_data_dir = None
        self.pkey = None
        self.rm_basedir = None
        self.transport = None

        self.load_config()

    #  when the meta data is in sync we should not need this
    # It could be used as consistency check
    # pl = [gf.rpath for gf in gfl]
    def get_gfile_list(self, rdir):
        """
        create a sorted list of paths to all generalized files
        :param sftp:
        :param rdir: remote directory (absolute path)
        :return:
        """

        if not rdir.startswith('/'):
            rdir = "/" + rdir

        result = []

        self.sftp.chdir(rdir)
        flist = self.sftp.listdir_attr()

        for f in flist:
            rpath = "%s/%s" % (rdir, f.filename)
            print(rpath)
            gf = GeneralizedFile(rpath)
            if stat.S_ISREG(f.st_mode):
                # regular file
                gf.isfile(True)
            elif stat.S_ISDIR(f.st_mode):
                # directory
                gf.isdir(True)
                # recursively call this function
                result.extend(self.get_gfile_list(rpath))
            else:
                # unknown mode
                msg = "Unknown mode (%s) for file: '%s'" % (f.st_mode, f.filename)
                raise ValueError(msg)

            result.append(gf)

        # sort by remote path
        result.sort(key=lambda _gf: _gf.rpath)
        return result

    def open_sftp(self):
        self.transport = paramiko.Transport((self.host, self.port))
        self.transport.connect(username=self.username, pkey=self.pkey)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def close(self):
        self.sftp.close()
        self.transport.close()

    def load_config(self):
        self.config = fsu.config
        self.host = self.config.host
        self.port = int(self.config.port)
        self.username = self.config.remote_user
        self.local_aux_dir = self.config.local_aux_dir
        self.local_data_dir = self.config.local_data_dir
        self.pkey = paramiko.RSAKey.from_private_key_file(self.config.ssh_key_path)
        self.rm_basedir = self.config.remote_base_dir
        if not self.rm_basedir.startswith('/'):
            self.rm_basedir = "/" + self.rm_basedir

        self.nrmd_path = os.path.join(self.local_aux_dir, fsu.NEW_REMOTE_META_DATA_FNAME)
        self.ormd_path = os.path.join(self.local_aux_dir, fsu.OLD_REMOTE_META_DATA_FNAME)
        self.lmd_path = os.path.join(self.local_aux_dir, fsu.META_DATA_FNAME)

    def cmp_rem2loc_by_md(self, new_old):
        """
        compare remote to local by comparing the metadata. Find out which files
        have changed

        :new_old:   either "new" or "old"; specifies which remote metadata is
                    to use

        :return:
        """

        if new_old == "new":
            rmd = fsu.read_json(self.nrmd_path)['files']
        elif new_old == "old":
            rmd = fsu.read_json(self.ormd_path)['files']
        else:
            raise ValueError("Invalid value for new_new_old: " + str(new_old))

        lmd = fsu.read_json(self.lmd_path)['files']

        rkeys = set(fsu.normalize_paths(rmd.keys(), self.local_data_dir))
        lkeys = set(fsu.normalize_paths(lmd.keys(), self.local_data_dir))

        common_files = rkeys.intersection(lkeys)
        missing_local = rkeys - common_files
        missing_remote = lkeys - common_files

        log.msg("locally missing files: ", missing_local)
        log.msg("remotely missing files: ", missing_remote)

        # now find changed files

        IPS()

    def pull_info(self):
        """
        pulls metada from remote and compares it to local metadata

        :return:
        """

        self.open_sftp()

        # pdx meta data path
        mdp = "%s/%s" % (self.rm_basedir, fsu.META_DATA_FNAME)

        # now find out which files have changed

        # ensure that target path exists
        fsu.mkdir_p(self.local_aux_dir)

        # download remote metadata to a local copy (will be "new metadata")

        try:
            self.sftp.get(mdp, self.nrmd_path)
        except FileNotFoundError as ex:
            log.err('probdox metadata not found. Cannot proceed. Please contact admin')
            self.close()
            msg = "File not found in server: " + mdp
            raise FileNotFoundError(msg)

        # compare remote to local
        self.cmp_rem2loc_by_md('new')
        # IPS()

        self.close()


def keygen():
    pass
    # ssh-keygen -t rsa -b 4096 -C "label" -f ./pdx-key


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(description='control a probdox repository')
    parser.add_argument('command', help='one of the following commands: push | pull | status | keygen')

    args = parser.parse_args()
    print(args.command)

    manager = Manager()

    if args.command == 'pull-info':
        manager.pull_info()
