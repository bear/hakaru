#/usr/bin/env python

VERSION = (0, 2, 0, "")

__author__    = 'Mike Taylor'
__contact__   = 'bear@bear.im'
__copyright__ = 'Copyright (c) by Mike Taylor'
__license__   = 'MIT'
__version__   = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])


from hakaru.tools import *
from hakaru.monitor import *
from hakaru.loghandler import *
