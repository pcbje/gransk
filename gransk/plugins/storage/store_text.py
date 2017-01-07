#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import logging
import io

import gransk.core.document as document
import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper


LOGGER = logging.getLogger(__name__)


class Subscriber(abstract_subscriber.Subscriber):
  """
  A class for writing extracted tect to file. Useful when debugging or
  implementing custom processing steps.
  """
  CONSUMES = [helper.FINISH_DOCUMENT]

  def setup(self, config):
    """
    Determine target directory.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    self.root = os.path.join(config[helper.DATA_ROOT], 'text')
    if not os.path.exists(self.root):
      try:
        os.makedirs(self.root)
      except Exception as err:
        LOGGER.exception("could not create dir %s: %s", self.root, err)

  def consume(self, doc, payload):
    """
    Write text to target directory, using a combination of filename and file
    ID as path.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    new_filename = '%s-%s' % \
      (doc.docid[0:8], document.secure_path(os.path.basename(doc.path)))

    if not os.path.exists(self.root):
      os.makedirs(self.root)

    new_path = os.path.join(self.root, new_filename)

    with io.open(new_path, 'w', encoding='utf-8') as out:
      out.write(doc.text)

    doc.meta['text_file'] = new_path
