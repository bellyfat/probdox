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

import argparse
import configparser
import os
from IPython import embed as IPS


def load_config():
    complete_config = configparser.ConfigParser()
    complete_config.read('config.ini')

    # create a shorthand for the default config
    config = complete_config['DEFAULT']

    return config


def pull():
    config = load_config()


def main():
    parser = argparse.ArgumentParser(description='control a probdox repository')
    parser.add_argument('command', help='one of the following commands: push | pull | status')

    args = parser.parse_args()
    print(args.command)

    if args.command == 'pull':
        pull()

    IPS()

if __name__ == "__main__":
    main()
