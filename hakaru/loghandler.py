#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:copyright: (c) 2013 by Mike Taylor
:license: MIT, see LICENSE for more details.

Establish a multiprocessing based Queue for other pieces of the
hakaru system to send log events so they can be safely written to disk

The idea for this was inspired by Vinay Sajip's blog post
  http://plumberjack.blogspot.com/2010/09/using-logging-with-multiprocessing.html
"""

import os, sys
import logging
import logging.handlers
import traceback

from Queue import Empty
from multiprocessing import Process, Queue, current_process


_fileFormat = '%(asctime)s %(levelname)-8s %(processName)-10s %(name)s %(message)s'
_echoFormat = '%(asctime)s %(levelname)-8s %(processName)-10s %(name)s %(message)s'
_fileSize   = 1000000
_fileCount  = 10
logQueue    = Queue()

class QueueLogHandler(logging.Handler):
    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue
        
    def emit(self, record):
        try:
            item = record.exc_info
            if item:
                _ = self.format(record)
                record.exc_info = None
            self.queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def echoLog(logger, format):
    console   = logging.StreamHandler()
    formatter = logging.Formatter(format)
    console.setFormatter(formatter)
    logger.addHandler(console)

def fileLog(logger, filename, filesize, count, format):
    handler    = logging.handlers.RotatingFileHandler(filename, 'a', filesize, count)
    formatter  = logging.Formatter(format)
    handler.setFormatter(formatter)
    log.addHandler(handler)

def handleLogEvents(inbound, config):
    filename   = config.get('filename',   None)
    filesize   = config.get('logsize',    _fileSize)
    filecount  = config.get('logcount',   _fileCount)
    fileformat = config.get('fileformat', _fileFormat)
    echoformat = config.get('echoformat', _echoFormat)
    logecho    = config.get('echo',       False)
    log        = logging.getLogger()

    if logecho:
        echoLog(log, echoformat)
    if filename is not None:
        fileLog(log, filename, filesize, filecount, fileformat)

    while True:
        try:
            entry = inbound.get()
            if entry is None:
                break
            logger = logging.getLogger(entry.name)
            logger.handle(entry)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print >> sys.stderr, 'exception raised inside of handleLogEvents()'
            traceback.print_exc(file=sys.stderr)

def start(config):
    """Start the global log handler for hakaru

    config is a Dict with the following entries and their default values:
      { "filename":  None,
        "logsize":   1000000,
        "logcount":  10,
        "logecho":   False,
        "fileformat: "%(asctime)s %(levelname)-8s %(processName)-10s %(name)s %(message)s"
        "echoformat: "%(asctime)s %(levelname)-8s %(processName)-10s %(name)s %(message)s"
      }

    NOTE: this will start a listener process to handle all log events
    """
    listener = Process(target=handleLogEvents, args=(logQueue, config.get('log', {})))
    listener.start()
