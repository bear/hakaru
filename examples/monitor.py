#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:copyright: (c) 2013 by Mike Taylor
:license: MIT, see LICENSE for more details.
"""

import os, sys
import json
import argparse

import hakaru


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('configFile')

    args = parser.parse_args()

    configFile = os.path.abspath(os.path.expanduser(args.configFile))

    if os.path.exists(configFile):
        config = json.load(open(configFile, 'r'))

        hakaru.loghandler.start(config)

        hakaru.monitor.start(config)
