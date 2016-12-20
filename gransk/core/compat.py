#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Python 2/3 compatibility module"""

import sys

if sys.version_info < (3,):
  reload(sys)
  sys.setdefaultencoding('utf-8')
