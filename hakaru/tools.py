#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:copyright: (c) 2013 by Mike Taylor
:license: MIT, see LICENSE for more details.

Gather metrics from a server and push to collection endpoint
"""

import os, sys

import redis


def getRedis(config):
    if 'redis' in config:
        cfg = config['redis']
    else:
        cfg = config
    host     = cfg.get('host', '127.0.0.1')
    port     = cfg.get('port', 6379)
    database = cfg.get('db',   0)

    return redis.StrictRedis(host=host, port=port, db=database)
