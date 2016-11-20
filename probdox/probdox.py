#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The code in this file is in Python 3 syntax

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
import argparse
import paramiko
import stat
from probdox.util.fsutils import log, GeneralizedFile, load_config, META_DATA_FNAME

from IPython import embed as IPS

# The code in this file is in Python 3 syntax
# ensure the right interpreter is used
assert sys.version_info[0] == 3


def get_gfile_list(sftp, rdir):
    """
    create a sorted list of paths to all generalized files
    :param sftp:
    :param rdir: remote directory (absolute path)
    :return:
    """

    if not rdir.startswith('/'):
        rdir = "/" + rdir

    result = []

    sftp.chdir(rdir)
    flist = sftp.listdir_attr()

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
            result.extend(get_gfile_list(sftp, rpath))
        else:
            # unknown mode
            msg = "Unknown mode (%s) for file: '%s'" % (f.st_mode, f.filename)
            raise ValueError(msg)

        result.append(gf)

    # sort by remote path
    result.sort(key=lambda _gf: _gf.rpath)
    return result


def pull():
    config = load_config()
    host = config['host']
    port = int(config['port'])
    username = config['remote_user']
    pkey = paramiko.RSAKey.from_private_key_file(config['ssh_key_path'])

    transport = paramiko.Transport((host, port))
    transport.connect(username=username, pkey=pkey)
    sftp = paramiko.SFTPClient.from_transport(transport)

    basedir = config['remote_base_dir']
    if not basedir.startswith('/'):
        basedir = "/" + basedir
    gfl = get_gfile_list(sftp, basedir)

    # list with paths only
    pl = [gf.rpath for gf in gfl]

    # pdx file list path
    pdx_flp = basedir + META_DATA_FNAME

    if pdx_flp not in pl:
        log.err('probdox metadata not found. Cannot proceed. Please contact admin')

        sftp.close()
        transport.close()

        return
    

    sftp.close()
    transport.close()


def keygen():
    pass
    # ssh-keygen -t rsa -b 4096 -C "label" -f ./pdx-key


def main():
    parser = argparse.ArgumentParser(description='control a probdox repository')
    parser.add_argument('command', help='one of the following commands: push | pull | status | keygen')

    args = parser.parse_args()
    print(args.command)

    if args.command == 'pull':
        pull()

    IPS()

if __name__ == "__main__":
    main()
