#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import unittest
import sys

logging.getLogger('elasticsearch').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

logging.basicConfig(
    format=u'[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO,
    datefmt=u'%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
  test_suite = unittest.TestLoader().discover('gransk', pattern='*_test.py')
  test_results = unittest.TextTestRunner(verbosity=2).run(test_suite)
  if not test_results.wasSuccessful():
    sys.exit(1)
