#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys

import gransk.core.helper as helper


class Collector(object):
  """Class for collecting paths from filesystem."""

  def __init__(self, config):
    self.in_filter = config.get(helper.IN_FILTER, [])
    self.end_filter = config.get(helper.END_FILTER, [])
    self.negate = config.get(helper.NEGATE, False)

  def _accept(self, path):
    lower_path = path.lower()
    is_in = any([fi.lower() in lower_path for fi in self.in_filter])
    is_end = any([lower_path.endswith(fi.lower()) for fi in self.end_filter])

    if os.path.basename(path).startswith('.'):
      return False

    empty_filter = len(
        self.in_filter) == 0 and len(
        self.end_filter) == 0

    valid = empty_filter or is_in or is_end

    if self.negate:
      valid = not valid

    return valid

  def collect(self, root_path):
    """
    Collect all files matching a path recursively.

    :param root_path: Input path. May point to a file or directory.
    :returns: Iterator of found paths.
    """
    invalid_start = os.sep + '.'
    included = 0
    total = 0

    if os.path.isdir(root_path):
      for folder, _, files in os.walk(root_path):
        if invalid_start in folder:
          continue

        for filename in files:
          path = os.path.join(folder, filename)
          if self._accept(path):
            included += 1
            yield path
          total += 1
          if total % 100 == 0:
            sys.stdout.write('\rFiles: %s (total: %s)' % (included, total))
            sys.stdout.flush()

    elif self._accept(root_path):
      yield root_path
